import os
import sys
import ctypes
import logging
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import List, Union, Tuple, Optional
from PIL import Image

# Import generated protobuf classes
from .protos.chrome_screen_ai_pb2 import VisualAnnotation as PBVisualAnnotation
from .protos.view_hierarchy_pb2 import ViewHierarchy as PBViewHierarchy
from .downloader import get_default_model_dir, get_binary_name

logger = logging.getLogger("google_screen_ai.engine")

# === Structs for Skia SkBitmap ===
class SkColorInfo(ctypes.Structure):
    _fields_ = [
        ('fColorSpace', ctypes.c_void_p),
        ('fColorType', ctypes.c_int32),
        ('fAlphaType', ctypes.c_int32)
    ]

class SkISize(ctypes.Structure):
    _fields_ = [
        ('fWidth', ctypes.c_int32),
        ('fHeight', ctypes.c_int32)
    ]

class SkImageInfo(ctypes.Structure):
    _fields_ = [
        ('fColorInfo', SkColorInfo),
        ('fDimensions', SkISize)
    ]

class SkPixmap(ctypes.Structure):
    _fields_ = [
        ('fPixels', ctypes.c_void_p),
        ('fRowBytes', ctypes.c_size_t),
        ('fInfo', SkImageInfo)
    ]

class SkBitmap(ctypes.Structure):
    _fields_ = [
        ('fPixelRef', ctypes.c_void_p),
        ('fPixmap', SkPixmap),
        ('fFlags', ctypes.c_uint32)
    ]


# === Python Dataclasses for API outputs ===
@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int
    angle: float

@dataclass
class SymbolBox:
    text: str
    bounding_box: Rect
    confidence: float

@dataclass
class WordBox:
    text: str
    bounding_box: Rect
    language: str
    confidence: float
    symbols: List[SymbolBox]

@dataclass
class LineBox:
    text: str
    bounding_box: Rect
    language: str
    confidence: float
    words: List[WordBox]
    paragraph_id: int
    block_id: int

@dataclass
class OCRResult:
    text: str
    lines: List[LineBox]
    raw_proto: Optional[PBVisualAnnotation] = None


class ScreenAI:
    """Python wrapper for Google ScreenAI library."""
    
    def __init__(self, model_dir: Union[str, Path] = None):
        """
        Initialize the ScreenAI engine by loading the DLL/SO library.
        
        Args:
            model_dir: Path to the directory where models are located.
                       If None, default ~/.config/screen_ai is used.
        """
        if model_dir is None:
            model_dir = get_default_model_dir()
            
        self.model_dir = Path(model_dir)
        self.resource_dir = self.model_dir / "resources"
        
        lib_name = get_binary_name()
        self.lib_path = self.resource_dir / lib_name
        
        if not self.lib_path.exists():
            raise FileNotFoundError(
                f"ScreenAI library not found at {self.lib_path}. "
                "Please run downloader.download_screen_ai() first."
            )
            
        self._lock = threading.Lock()
        self._ocr_initialized = False
        self._mce_initialized = False
        self._max_image_dimension = 2048
        
        # Load the dynamic library
        mode = os.RTLD_LAZY if hasattr(os, 'RTLD_LAZY') else ctypes.DEFAULT_MODE
        try:
            self._lib = ctypes.CDLL(str(self.lib_path), mode=mode)
        except Exception as e:
            logger.error(f"Failed to load dynamic library {self.lib_path}: {e}")
            raise
            
        self._setup_bindings()
        self._setup_callbacks()
        
    def _setup_bindings(self):
        """Configure ctypes arguments and return types for the library functions."""
        # General functions
        self._lib.GetLibraryVersion.argtypes = [ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
        self._lib.GetLibraryVersion.restype = None
        
        self._lib.EnableDebugMode.argtypes = []
        self._lib.EnableDebugMode.restype = None
        
        self._lib.SetFileContentFunctions.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._lib.SetFileContentFunctions.restype = None
        
        self._lib.FreeLibraryAllocatedCharArray.argtypes = [ctypes.c_void_p]
        self._lib.FreeLibraryAllocatedCharArray.restype = None
        
        self._lib.FreeLibraryAllocatedInt32Array.argtypes = [ctypes.c_void_p]
        self._lib.FreeLibraryAllocatedInt32Array.restype = None
        
        # OCR functions
        self._lib.InitOCRUsingCallback.argtypes = []
        self._lib.InitOCRUsingCallback.restype = ctypes.c_bool
        
        self._lib.SetOCRLightMode.argtypes = [ctypes.c_bool]
        self._lib.SetOCRLightMode.restype = None
        
        self._lib.GetMaxImageDimension.argtypes = []
        self._lib.GetMaxImageDimension.restype = ctypes.c_uint32
        
        self._lib.PerformOCR.argtypes = [ctypes.POINTER(SkBitmap), ctypes.POINTER(ctypes.c_uint32)]
        self._lib.PerformOCR.restype = ctypes.c_void_p
        
        # Main Content Extraction functions
        self._lib.InitMainContentExtractionUsingCallback.argtypes = []
        self._lib.InitMainContentExtractionUsingCallback.restype = ctypes.c_bool
        
        self._lib.ExtractMainContent.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self._lib.ExtractMainContent.restype = ctypes.c_void_p
        
        # Uninitialization functions (if available in DLL)
        if hasattr(self._lib, "UninitializeOCR"):
            self._lib.UninitializeOCR.argtypes = []
            self._lib.UninitializeOCR.restype = None
        if hasattr(self._lib, "UninitializeMainContentExtraction"):
            self._lib.UninitializeMainContentExtraction.argtypes = []
            self._lib.UninitializeMainContentExtraction.restype = None

    def _setup_callbacks(self):
        """Set up and pin the callbacks for reading the model files through Python."""
        @ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_char_p)
        def cb_size(p):
            filename_str = p.decode('utf-8')
            path = self.resource_dir / filename_str
            return os.path.getsize(path) if path.exists() else 0

        @ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_void_p)
        def cb_read(p, size, ptr):
            filename_str = p.decode('utf-8')
            path = self.resource_dir / filename_str
            if path.exists():
                with open(path, 'rb') as f:
                    ctypes.memmove(ptr, f.read(size), size)

        # Pin callbacks to the instance to avoid GC sweep
        self._cb_size = cb_size
        self._cb_read = cb_read
        
        # Set the callbacks in the library
        self._lib.SetFileContentFunctions(self._cb_size, self._cb_read)

    def get_version(self) -> Tuple[int, int]:
        """Return the library version as (major, minor) tuple."""
        major = ctypes.c_uint32(0)
        minor = ctypes.c_uint32(0)
        self._lib.GetLibraryVersion(ctypes.byref(major), ctypes.byref(minor))
        return (major.value, minor.value)
        
    def enable_debug_mode(self):
        """Enable library debug mode."""
        self._lib.EnableDebugMode()

    def init_ocr(self, light_mode: bool = False) -> bool:
        """
        Initialize the OCR engine.
        
        Args:
            light_mode: Set to True to enable the light-mode OCR pipeline.
        """
        with self._lock:
            if self._ocr_initialized:
                self._lib.SetOCRLightMode(light_mode)
                return True
                
            logger.info("Initializing ScreenAI OCR subsystem...")
            success = self._lib.InitOCRUsingCallback()
            if success:
                self._lib.SetOCRLightMode(light_mode)
                self._max_image_dimension = self._lib.GetMaxImageDimension()
                self._ocr_initialized = True
                logger.info("ScreenAI OCR subsystem successfully initialized.")
            else:
                logger.error("Failed to initialize ScreenAI OCR subsystem.")
            return success

    def init_main_content_extraction(self) -> bool:
        """Initialize the Main Content Extraction engine."""
        with self._lock:
            if self._mce_initialized:
                return True
                
            logger.info("Initializing ScreenAI Main Content Extraction subsystem...")
            success = self._lib.InitMainContentExtractionUsingCallback()
            if success:
                self._mce_initialized = True
                logger.info("ScreenAI Main Content Extraction subsystem successfully initialized.")
            else:
                logger.error("Failed to initialize ScreenAI Main Content Extraction subsystem.")
            return success

    def perform_ocr(self, image: Union[Image.Image, Path, str], light_mode: bool = False) -> Optional[OCRResult]:
        """
        Run OCR on the provided PIL Image or file path.
        
        Args:
            image: A PIL Image or Path/str to an image file.
            light_mode: Whether to run in light mode (updates config dynamically).
        """
        if not self._ocr_initialized:
            if not self.init_ocr(light_mode):
                raise RuntimeError("OCR subsystem could not be initialized.")
                
        # Update light mode if needed
        self._lib.SetOCRLightMode(light_mode)
        
        # Load image if file path is provided
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        else:
            img = image
            
        # Downsample if it exceeds max dimension
        w, h = img.size
        if max(w, h) > self._max_image_dimension:
            scale = self._max_image_dimension / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            logger.debug(f"Resizing image from {w}x{h} to {new_w}x{new_h} to match max dimension.")
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            w, h = img.size
            
        # Convert image to RGBA bytes
        rgba_img = img.convert("RGBA")
        raw_bytes = rgba_img.tobytes()
        
        # Prepare SkBitmap
        bmp = SkBitmap()
        bmp.fPixmap.fPixels = ctypes.cast(ctypes.c_char_p(raw_bytes), ctypes.c_void_p)
        bmp.fPixmap.fRowBytes = w * 4
        bmp.fPixmap.fInfo.fColorInfo.fColorType = 4  # kRGBA_8888
        bmp.fPixmap.fInfo.fColorInfo.fAlphaType = 1   # kPremul
        bmp.fPixmap.fInfo.fDimensions.fWidth = w
        bmp.fPixmap.fInfo.fDimensions.fHeight = h
        
        # Run OCR
        out_len = ctypes.c_uint32(0)
        with self._lock:
            result_ptr = self._lib.PerformOCR(ctypes.byref(bmp), ctypes.byref(out_len))
            
        if not result_ptr:
            logger.warning("PerformOCR returned a null pointer.")
            return None
            
        try:
            proto_bytes = ctypes.string_at(result_ptr, out_len.value)
            
            # Parse proto message
            pb_ann = PBVisualAnnotation()
            pb_ann.ParseFromString(proto_bytes)
            
            # Parse into custom dataclasses
            lines_list = []
            all_text_lines = []
            
            for line_pb in pb_ann.lines:
                words_list = []
                for word_pb in line_pb.words:
                    symbols_list = []
                    for sym_pb in word_pb.symbols:
                        rect_pb = sym_pb.bounding_box
                        symbols_list.append(SymbolBox(
                            text=sym_pb.utf8_string,
                            bounding_box=Rect(rect_pb.x, rect_pb.y, rect_pb.width, rect_pb.height, rect_pb.angle),
                            confidence=sym_pb.confidence
                        ))
                    
                    rect_w = word_pb.bounding_box
                    words_list.append(WordBox(
                        text=word_pb.utf8_string,
                        bounding_box=Rect(rect_w.x, rect_w.y, rect_w.width, rect_w.height, rect_w.angle),
                        language=word_pb.language,
                        confidence=word_pb.confidence,
                        symbols=symbols_list
                    ))
                
                rect_l = line_pb.bounding_box
                lines_list.append(LineBox(
                    text=line_pb.utf8_string,
                    bounding_box=Rect(rect_l.x, rect_l.y, rect_l.width, rect_l.height, rect_l.angle),
                    language=line_pb.language,
                    confidence=line_pb.confidence,
                    words=words_list,
                    paragraph_id=line_pb.paragraph_id,
                    block_id=line_pb.block_id
                ))
                if line_pb.utf8_string.strip():
                    all_text_lines.append(line_pb.utf8_string.strip())
                    
            full_text = "\n".join(all_text_lines)
            return OCRResult(text=full_text, lines=lines_list, raw_proto=pb_ann)
        finally:
            self._lib.FreeLibraryAllocatedCharArray(result_ptr)

    def extract_main_content(self, view_hierarchy: Union[bytes, PBViewHierarchy]) -> List[int]:
        """
        Extract main content node IDs from the view hierarchy.
        
        Args:
            view_hierarchy: Serialized protobuf bytes or a ViewHierarchy protobuf object.
        """
        if not self._mce_initialized:
            if not self.init_main_content_extraction():
                raise RuntimeError("Main Content Extraction subsystem could not be initialized.")
                
        if isinstance(view_hierarchy, PBViewHierarchy):
            serialized_bytes = view_hierarchy.SerializeToString()
        else:
            serialized_bytes = view_hierarchy
            
        nodes_count = ctypes.c_uint32(0)
        with self._lock:
            result_ptr = self._lib.ExtractMainContent(
                serialized_bytes,
                len(serialized_bytes),
                ctypes.byref(nodes_count)
            )
            
        if not result_ptr:
            logger.warning("ExtractMainContent returned a null pointer.")
            return []
            
        try:
            # Read dynamic int32 array from memory
            int_array_type = ctypes.c_int32 * nodes_count.value
            int_array = int_array_type.from_address(result_ptr)
            return list(int_array)
        finally:
            self._lib.FreeLibraryAllocatedInt32Array(result_ptr)

    def close(self):
        """Cleanly uninitialize and unload models to free memory."""
        with self._lock:
            if self._ocr_initialized and hasattr(self._lib, "UninitializeOCR"):
                logger.info("Uninitializing ScreenAI OCR...")
                self._lib.UninitializeOCR()
                self._ocr_initialized = False
            if self._mce_initialized and hasattr(self._lib, "UninitializeMainContentExtraction"):
                logger.info("Uninitializing ScreenAI Main Content Extraction...")
                self._lib.UninitializeMainContentExtraction()
                self._mce_initialized = False

    def __enter__(self) -> "ScreenAI":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except:
            pass
