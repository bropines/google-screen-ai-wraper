# Python API Documentation — google-screen-ai-wraper

This document provides a detailed reference for all classes, methods, and data structures available in the `google_screen_ai` package.

---

## 📥 Asset Downloader Function

### `download_screen_ai(model_dir=None, force=False) -> bool`
Downloads and extracts the dynamic library (`chrome_screen_ai`) and TFLite/FST model assets from Google's CIPD registry matching the current OS and CPU architecture.

* **Parameters:**
  * `model_dir` (*str | Path*, optional): Directory to download and export the model assets and library to. If `None`, defaults to `~/.config/screen_ai/`.
  * `force` (*bool*, optional): If `True`, forces a re-download and overwrites any existing files.
* **Returns:** `True` if installation is successful or already present, `False` otherwise.

---

## ⚙️ The `ScreenAI` Engine Class

The primary class representing Google's ScreenAI engine. It is recommended to use this class as a context manager to ensure automatic memory and model unloading.

### Initialization
```python
from google_screen_ai import ScreenAI
engine = ScreenAI(model_dir=None)
```
* **Parameters:**
  * `model_dir` (*str | Path*, optional): Directory where the models and dynamic library are located. Must match the directory passed to `download_screen_ai`.

---

### Class Methods

#### `get_version() -> Tuple[int, int]`
Returns the major and minor version numbers of the loaded Google ScreenAI dynamic library.
* **Returns:** A tuple of `(major, minor)`, e.g., `(148, 11)`.

#### `init_ocr() -> bool`
Initializes the OCR subsystem (loads text detection models and preloads FST recognition models).
* **Returns:** `True` if initialization succeeded.

#### `init_main_content_extraction() -> bool`
Initializes the Main Content Extraction subsystem (loads page/layout structures models).
* **Returns:** `True` if initialization succeeded.

#### `set_light_mode(enable: bool) -> None`
Enables or disables OCR Light Mode.
* **Parameters:**
  * `enable` (*bool*): Set to `True` for faster inference (lower resource consumption), or `False` for maximum quality.

#### `perform_ocr(image: Union[str, Path, PIL.Image.Image, np.ndarray]) -> Optional[OCRResult]`
Runs the OCR engine on the provided image.
* **Parameters:**
  * `image`: Path to the image file, a `PIL.Image` object, or a `numpy.ndarray` (BGR/RGB format).
* **Returns:** An `OCRResult` object if successful, or `None` if the operation failed.

#### `extract_main_content(view_hierarchy: Union[bytes, ViewHierarchy]) -> List[int]`
Identifies main content blocks inside a page's visual/DOM node tree (view hierarchy).
* **Parameters:**
  * `view_hierarchy`: Serialized protobuf bytes or a `ViewHierarchy` protobuf object.
* **Returns:** A list of UI element `ID`s corresponding to the primary content blocks.

#### `close() -> None`
Unloads the neural models from RAM and frees C++ buffers immediately. Call this if you manage the `ScreenAI` instance lifetime manually without a `with` statement.

---

## 📦 Data Structures (Dataclasses)

### `OCRResult`
Represents the complete OCR output for an image.
* **Fields:**
  * `text` (*str*): Reconstructed plain text representing the entire image.
  * `lines` (*List[LineBox]*): List of detected text lines in reading order.
  * `raw_proto` (*VisualAnnotation*): The raw parsed protobuf output from Google's native DLL.

---

### `LineBox`
Represents a single recognized line of text.
* **Fields:**
  * `text` (*str*): The recognized text string of this line.
  * `bounding_box` (*Rect*): Bounding box of the line on the image.
  * `language` (*str*): Guessed language code in ISO 639-1 format (e.g. `"ja"`, `"ru"`, `"en"`).
  * `confidence` (*float*): The model's confidence score (`0.0` to `1.0`).
  * `words` (*List[WordBox]*): List of individual words contained in this line.
  * `paragraph_id` (*int*): ID of the paragraph this line belongs to.
  * `block_id` (*int*): ID of the layout block.

---

### `WordBox`
Represents a single word in a text line.
* **Fields:**
  * `text` (*str*): The word text.
  * `bounding_box` (*Rect*): Word coordinates.
  * `language` (*str*): Word language code (ISO 639-1).
  * `confidence` (*float*): Word recognition confidence.
  * `symbols` (*List[SymbolBox]*): Individual characters/symbols in this word.

---

### `SymbolBox`
Represents an individual character or symbol.
* **Fields:**
  * `text` (*str*): The character.
  * `bounding_box` (*Rect*): Coordinates of the character.
  * `confidence` (*float*): Character confidence score.

---

### `Rect`
Represents a bounding box coordinate rectangle.
* **Fields:**
  * `x` (*int*): Left boundary offset (in pixels).
  * `y` (*int*): Top boundary offset (in pixels).
  * `w` (*int*): Width of the box.
  * `h` (*int*): Height of the box.

---

## 💡 Quickstart Examples

### Example 1: Context Manager Usage (Recommended)
```python
from google_screen_ai import download_screen_ai, ScreenAI

# 1. Download models to default location
download_screen_ai()

# 2. Run OCR using context manager (safely unloads models when finished)
with ScreenAI() as engine:
    engine.init_ocr()
    result = engine.perform_ocr("manga_raw.jpg")
    
    if result:
        print("Recognized Text:")
        print(result.text)
```

### Example 2: Language Filtering and Coordinates
```python
with ScreenAI() as engine:
    engine.init_ocr()
    result = engine.perform_ocr("screenshot.png")
    
    for line in result.lines:
        # Process only Japanese text lines
        if line.language == "ja":
            print(f"Japanese Line: '{line.text}' (Conf: {line.confidence:.2%})")
            bbox = line.bounding_box
            print(f"BBox: X={bbox.x}, Y={bbox.y}, W={bbox.w}, H={bbox.h}")
```
