import sys
import json
import argparse
from pathlib import Path
from dataclasses import asdict

from .downloader import download_screen_ai, is_installed, get_cipd_platform
from .engine import ScreenAI

def handle_download(args):
    """Download ScreenAI binaries and models."""
    model_dir = Path(args.dir) if args.dir else None
    success = download_screen_ai(model_dir=model_dir, force=args.force)
    if success:
        print("Success: ScreenAI binaries and models downloaded successfully.")
        sys.exit(0)
    else:
        print("Error: Failed to download ScreenAI binaries and models.")
        sys.exit(1)

def handle_ocr(args):
    """Run OCR on a provided image file."""
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)
        
    model_dir = Path(args.dir) if args.dir else None
    if not is_installed(model_dir):
        print(f"Error: ScreenAI is not installed at {model_dir or 'default location'}. Run 'download' command first.", file=sys.stderr)
        sys.exit(1)
        
    try:
        engine = ScreenAI(model_dir=model_dir)
        # Enable debug mode if verbose
        if args.verbose:
            engine.enable_debug_mode()
            
        result = engine.perform_ocr(image_path, light_mode=args.light)
        if result is None:
            print("Error: OCR returned no results.", file=sys.stderr)
            sys.exit(1)
            
        if args.format == "text":
            print(result.text)
        elif args.format == "json":
            # Convert dataclass to dict and format it to JSON
            # Ignore raw_proto as it's not JSON serializable directly
            res_dict = asdict(result)
            res_dict.pop("raw_proto", None)
            print(json.dumps(res_dict, ensure_ascii=False, indent=2))
        elif args.format == "proto":
            print(str(result.raw_proto))
            
    except Exception as e:
        print(f"Error running OCR: {e}", file=sys.stderr)
        sys.exit(1)

def handle_extract(args):
    """Run Main Content Extraction on a serialized ViewHierarchy file."""
    proto_path = Path(args.proto)
    if not proto_path.exists():
        print(f"Error: ViewHierarchy proto file not found: {proto_path}", file=sys.stderr)
        sys.exit(1)
        
    model_dir = Path(args.dir) if args.dir else None
    if not is_installed(model_dir):
        print(f"Error: ScreenAI is not installed. Run 'download' command first.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(proto_path, "rb") as f:
            proto_bytes = f.read()
            
        engine = ScreenAI(model_dir=model_dir)
        if args.verbose:
            engine.enable_debug_mode()
            
        node_ids = engine.extract_main_content(proto_bytes)
        print(json.dumps(node_ids))
    except Exception as e:
        print(f"Error running Main Content Extraction: {e}", file=sys.stderr)
        sys.exit(1)

def handle_info(args):
    """Print information about ScreenAI library."""
    model_dir = Path(args.dir) if args.dir else None
    installed = is_installed(model_dir)
    print(f"CIPD Platform Target: {get_cipd_platform()}")
    print(f"Installation Status: {'INSTALLED' if installed else 'NOT INSTALLED'}")
    
    if installed:
        try:
            engine = ScreenAI(model_dir=model_dir)
            version = engine.get_version()
            print(f"Library DLL path    : {engine.lib_path.resolve()}")
            print(f"Library DLL version : {version[0]}.{version[1]}")
        except Exception as e:
            print(f"Error reading library info: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Google ScreenAI Command-Line Interface Wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)
    
    # Download parser
    download_parser = subparsers.add_parser("download", help="Download ScreenAI library and models")
    download_parser.add_argument("-d", "--dir", help="Custom model target directory")
    download_parser.add_argument("-f", "--force", action="store_true", help="Force re-download even if already present")
    
    # OCR parser
    ocr_parser = subparsers.add_parser("ocr", help="Run OCR on an image")
    ocr_parser.add_argument("-i", "--image", required=True, help="Path to image file")
    ocr_parser.add_argument("-d", "--dir", help="Custom model directory path")
    ocr_parser.add_argument("--light", action="store_true", help="Enable light-mode OCR")
    ocr_parser.add_argument("--format", choices=["text", "json", "proto"], default="text", help="Output format (default: text)")
    ocr_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose library logging")
    
    # Extract parser
    extract_parser = subparsers.add_parser("extract", help="Extract main content node IDs from serialized ViewHierarchy")
    extract_parser.add_argument("-p", "--proto", required=True, help="Path to serialized view_hierarchy.proto file")
    extract_parser.add_argument("-d", "--dir", help="Custom model directory path")
    extract_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose library logging")
    
    # Info parser
    info_parser = subparsers.add_parser("info", help="Get installation and library info")
    info_parser.add_argument("-d", "--dir", help="Custom model directory path")
    
    args = parser.parse_args()
    
    if args.command == "download":
        handle_download(args)
    elif args.command == "ocr":
        handle_ocr(args)
    elif args.command == "extract":
        handle_extract(args)
    elif args.command == "info":
        handle_info(args)

if __name__ == "__main__":
    main()
