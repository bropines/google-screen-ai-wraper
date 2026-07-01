import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add current workspace directory to sys.path so we can import google_screen_ai local package
sys.path.insert(0, str(Path(__file__).parent))

from google_screen_ai import ScreenAI
from google_screen_ai.protos.view_hierarchy_pb2 import ViewHierarchy

def generate_test_image(text: str, filename: str = "temp_test_image.png") -> Path:
    """Generate a simple image containing the given text."""
    # Create white image
    img = Image.new("RGB", (600, 150), color="white")
    draw = ImageDraw.Draw(img)
    
    # Draw simple text
    draw.text((20, 50), text, fill="black")
    
    img_path = Path(__file__).parent / filename
    img.save(img_path)
    return img_path

def test_ocr(engine: ScreenAI):
    print("\n--- Testing ScreenAI OCR ---")
    test_text = "Google ScreenAI OCR Test Successful"
    img_path = generate_test_image(test_text)
    
    try:
        # Run OCR
        print(f"Running OCR on generated image...")
        result = engine.perform_ocr(img_path)
        
        if result is None:
            print("FAILED: OCR returned None.")
            return False
            
        print(f"Recognized text:\n{result.text}")
        print(f"Lines count: {len(result.lines)}")
        
        # Verify text content
        if "ScreenAI" in result.text:
            print("SUCCESS: OCR text validation passed.")
            return True
        else:
            print("FAILED: Expected keywords not found in OCR result.")
            return False
    finally:
        # Clean up
        if img_path.exists():
            img_path.unlink()

def test_main_content_extraction(engine: ScreenAI):
    print("\n--- Testing Main Content Extraction ---")
    try:
        # Build mock ViewHierarchy
        vh = ViewHierarchy()
        
        # Root node
        root = vh.ui_elements.add()
        root.id = 0
        root.parent_id = -1
        root.child_ids.extend([1, 2])
        
        # Child 1 (e.g. header/non-essential)
        c1 = vh.ui_elements.add()
        c1.id = 1
        c1.parent_id = 0
        
        # Child 2 (e.g. main content area)
        c2 = vh.ui_elements.add()
        c2.id = 2
        c2.parent_id = 0
        
        print("Running main content extraction on mock ViewHierarchy...")
        main_node_ids = engine.extract_main_content(vh)
        print(f"Extracted main content node IDs: {main_node_ids}")
        print("SUCCESS: Main content extraction completed.")
        return True
    except Exception as e:
        print(f"FAILED: Main content extraction raised an exception: {e}")
        return False

def main():
    # Use the downloaded binaries in workspace for testing
    model_dir = Path(__file__).parent.parent / "screen-ai-windows-amd64"
    print(f"Initializing ScreenAI engine with models at: {model_dir.resolve()}")
    
    try:
        with ScreenAI(model_dir=model_dir) as engine:
            version = engine.get_version()
            print(f"Loaded ScreenAI version: {version[0]}.{version[1]}")
            
            ocr_success = test_ocr(engine)
            mce_success = test_main_content_extraction(engine)
            
            if ocr_success and mce_success:
                print("\nALL TESTS PASSED SUCCESSFULLY!")
                sys.exit(0)
            else:
                print("\nSOME TESTS FAILED.")
                sys.exit(1)
            
    except Exception as e:
        print(f"\nFailed to initialize or run test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
