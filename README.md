# Google ScreenAI Python Wrapper & CLI

This repository contains a production-ready, cross-platform Python wrapper and CLI for Google's on-device **ScreenAI** OCR and Main Content Extraction library.

---

## Installation & Dependency Management

You can install the package locally using `pip` or `uv`.

### 1. Local Directory Installation

Navigate to the project root containing `setup.py` and run:

#### Using `pip`:
```bash
pip install -e ./google_screen_ai
```

#### Using `uv`:
```bash
uv pip install -e ./google_screen_ai
```

---

### 2. Git Remote Link Installation (Without local clone)

You can install this library directly into another project using its Git source URL.

#### Using `pip`:
```bash
pip install "git+https://github.com/yourusername/ScreenAI_OCR.git"
```

#### Using `uv`:
```bash
uv pip install "git+https://github.com/yourusername/ScreenAI_OCR.git"
```

---

### 3. Adding as Project Dependency using `uv`

If you manage your project using `uv` (`pyproject.toml` workspace environment), add it directly:

```bash
# Add as local path dependency
uv add --path ./google_screen_ai

# Add as remote Git dependency
uv add "git+https://github.com/yourusername/ScreenAI_OCR.git"
```

---

### 4. Running CLI Commands via `uv`

You can run ScreenAI CLI commands directly using `uv run`:

```bash
# Get library/DLL info
uv run screen-ai info

# Download Google ScreenAI binaries and models (~50MB)
uv run screen-ai download

# Run OCR on an image
uv run screen-ai ocr --image sample.png
```

---

## Project Structure

- `google_screen_ai/` — Core Python wrapper package.
  - `downloader.py` — Platform detection and CIPD downloader.
  - `engine.py` — Dynamic library `ctypes` bindings and API engine.
  - `protos/` — Compiled protobuf serializations (`chrome_screen_ai.proto` & `view_hierarchy.proto`).
  - `__main__.py` — Command-line interface logic.
- `test_wrapper.py` — Core automated library tests.
- `setup.py` — Setup script for `google_screen_ai`.
