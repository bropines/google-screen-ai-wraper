# Google ScreenAI Python Wrapper

Python binding for Google's on-device **ScreenAI** OCR and Main Content Extraction library. 

This library wraps the official `chrome_screen_ai` native binary distributed by Google through their Chrome infrastructure. It runs entirely on-device, offering fast CPU-based inference via the TensorFlow Lite XNNPACK delegate.

---

## Features

- **OCR Subsystem (`PerformOCR`):** Accurately recognizes multi-language text (including English, Russian, Japanese, etc.) and extracts bounding boxes, lines, words, characters, paragraph IDs, and confidence scores.
- **Main Content Extraction (`ExtractMainContent`):** Isolates the primary visual or DOM node blocks from a view hierarchy tree.
- **Automated Dependency Management:** Automatically detects current OS and architecture (Windows, macOS, Linux with x86_64, arm64, or 386) and exports matching libraries and model assets directly from Google CIPD servers.
- **Developer-Friendly Output:** Returns outputs as structured Python `dataclasses` rather than raw dicts or binary protobuf messages.
- **Memory & Thread Safe:** Safely handles ctypes callback pointers and releases all native C++ arrays via internal library calls to prevent memory leaks in Python.

---

## Installation & Dependency Management

### 1. Local Directory Installation

If you are developing locally or cloned this repository, install it into your active environment.

#### Using `pip`:
```bash
pip install -e .
```

#### Using `uv` (pip compatibility mode):
```bash
uv pip install -e .
```

---

### 2. Git Remote Link Installation (Without local clone)

You can install the package directly into any Python project using its Git source URL.

#### Using `pip`:
```bash
pip install "git+https://github.com/bropines/google-screen-ai-wraper.git"
```

#### Using `uv` (pip compatibility mode):
```bash
uv pip install "git+https://github.com/bropines/google-screen-ai-wraper.git"
```

---

### 3. Adding as Project Dependencies using `uv`

If you manage your project using `uv` (`pyproject.toml` workspace environment), add it directly as a project dependency:

#### Add local path:
```bash
uv add --path ./google-screen-ai-wraper
```

#### Add Git URL:
```bash
uv add "git+https://github.com/bropines/google-screen-ai-wraper.git"
```

---

### 4. Running CLI Commands via `uv`

If you are using `uv`, you can run the console script directly without activating the virtual environment:

```bash
# Get library/DLL info
uv run screen-ai info

# Download Google ScreenAI binaries and models
uv run screen-ai download

# Run OCR on an image
uv run screen-ai ocr --image manga_scan.png
```

---

## CLI Usage

The library includes a command-line interface `screen-ai` (available after installing via `setup.py`):

```bash
# Download dynamic library and models (~50MB) to default user location
screen-ai download

# Check version and installation status
screen-ai info

# Perform OCR on an image and print text
screen-ai ocr --image sample.png

# Perform OCR and output structured JSON data
screen-ai ocr --image sample.png --format json
```

---

## Quickstart Code Example

### 1. Optical Character Recognition (OCR)

```python
from PIL import Image
from google_screen_ai import download_screen_ai, ScreenAI

# 1. Download binaries & models (runs only if not installed)
download_screen_ai()

# 2. Load the engine
engine = ScreenAI()

# 3. Initialize OCR engine (loads models)
engine.init_ocr()

# 4. Perform OCR
result = engine.perform_ocr("manga_page.png")

if result:
    print(f"Recognized Text:\n{result.text}")
    for line in result.lines:
        print(f"Line: {line.text} (Confidence: {line.confidence:.2%})")
        for word in line.words:
            print(f"  Word: {word.text} at bbox ({word.bounding_box.x}, {word.bounding_box.y})")
```

### 2. Main Content Extraction (MCE)

```python
from google_screen_ai import ScreenAI
from google_screen_ai.protos.view_hierarchy_pb2 import ViewHierarchy

engine = ScreenAI()
engine.init_main_content_extraction()

# Create standard ViewHierarchy tree structure
vh = ViewHierarchy()
# Define your nodes...
# root = vh.ui_elements.add()
# root.id = 0
# root.child_ids.extend([1, 2])

# Extract primary/main content node indices
main_node_ids = engine.extract_main_content(vh)
print(f"Main Content Nodes: {main_node_ids}")
```
