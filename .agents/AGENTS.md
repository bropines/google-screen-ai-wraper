# Rules and Guidelines for google-screen-ai-wraper

This project is a lightweight, cross-platform Python binding and CLI wrapper for Google's on-device **ScreenAI** OCR and Main Content Extraction library.

---

## 🛠 Technology Stack & Core Design
- **Core:** Pure Python 3.8+ bindings interacting with the dynamic library (`chrome_screen_ai.dll` on Windows, `libchromescreenai.so` on macOS/Linux) using `ctypes`.
- **Packaging:** Standard `setuptools` (`setup.py`).
- **Protobuf:** Google's compiled protobuf files are located in `google_screen_ai/protos/` and must be compiled using `grpcio-tools`. Do not edit generated files manually.

---

## ⚠️ Critical Rules for AI Agents

### 1. Memory Management & Unloading
- Google's models occupy significant RAM (~50MB+).
- **Rule:** Always call `UninitializeOCR()` and `UninitializeMainContentExtraction()` when freeing the engine.
- Internally, this is handled by `ScreenAI.close()`. Users should be encouraged to use the engine as a context manager:
  ```python
  with ScreenAI() as engine:
      engine.init_ocr()
      # perform operations...
  ```
- Any modifications to the `engine.py` wrapper must preserve this cleanup behavior in `__del__` and `__exit__`.

### 2. Dependency & Asset Constraints
- **Rule:** Do NOT commit compiled binaries (`.dll`, `.so`, `.dylib`) or downloaded model files (`.tflite`, `.fst`, `.syms`) to the repository. They are ignored in `.gitignore`.
- Use the cross-platform downloader `google_screen_ai/downloader.py` to fetch binaries on-demand from Google's CIPD registry.
- Default download path is user-specific: `~/.config/screen_ai` (can be overridden by the user).

### 3. Portability & Paths
- **Rule:** Never use absolute paths (e.g. `F:/bropi/...`) in project source code, tests, or documentation. Use relative paths relative to the project root.

### 4. Language Auto-Detection
- ScreenAI automatically detects languages on-the-fly using an internal `langid` model.
- **Rule:** Do not expose manual language-setting arguments in OCR execution functions. The library automatically returns guessed language codes in `LineBox.language` and `WordBox.language` (in ISO 639-1 format like `"ja"`, `"ru"`, `"en"`).
