# Google ScreenAI Python Wrapper & CLI

This repository contains a production-ready, cross-platform Python wrapper and CLI for Google's on-device **ScreenAI** OCR and Main Content Extraction library.

---

## 📸 Automated ShareX Setup & Clipboard Integration

If you use **ShareX** on Windows, you can fully automate setup with a single command:

```bash
screen-ai --setup-sharex
```

* **Auto-Download:** Checks if ScreenAI binaries and models exist, downloading them automatically if missing.
* **Auto-Hotkey:** Configures **`Ctrl + Shift + S`** in ShareX to capture screen regions, run Google ScreenAI OCR on-device, and copy text directly to your clipboard.

### Clipboard Copy Flag
You can also copy OCR results directly to the clipboard from CLI using the `--sharex` / `-sx` flag:

```bash
screen-ai ocr -i sample.png --sharex
```

*Note: Install with `[clipboard]` extra for clipboard support:*
```bash
pip install -e .[clipboard]
```

---

## Installation & Dependency Management

You can install the package locally using `pip` or `uv`.

### 1. Local Directory Installation

Navigate to the project root containing `setup.py` and run:

```bash
pip install -e .[clipboard]
```

### 2. PyPI / Git Remote Link Installation

```bash
pip install "git+https://github.com/bropines/google-screen-ai-wraper.git#egg=google-screen-ai-wraper[clipboard]"
```

---

## CLI Usage Examples

```bash
# Get library DLL info & installation status
screen-ai info

# Download Google ScreenAI binaries and models (~50MB)
screen-ai download

# Run OCR on an image and print text
screen-ai ocr -i sample.png

# Run OCR and copy text directly to clipboard
screen-ai ocr -i sample.png --sharex

# Configure ShareX hotkey integration automatically
screen-ai --setup-sharex
```

---

## Project Structure

- `google_screen_ai/` — Core Python wrapper package.
  - `downloader.py` — Platform detection and CIPD downloader.
  - `engine.py` — Dynamic library `ctypes` bindings and API engine.
  - `protos/` — Canonical protobuf sources and generated serializations (`chrome_screen_ai.proto` & `view_hierarchy.proto`).
  - `utils/` — ShareX setup automation and clipboard helper functions.
  - `__main__.py` — Command-line interface logic.
- `docs/sharex.md` — Detailed ShareX configuration guide.
- `test_wrapper.py` — Core automated library tests.
- `setup.py` / `setup.cfg` / `pyproject.toml` — Package configuration for PyPI build and distribution.
