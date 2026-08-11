# ShareX Integration Guide for Google ScreenAI

You can integrate `google-screen-ai-wraper` with **ShareX** to perform high-speed on-device OCR on screen captures and automatically copy the recognized text to your clipboard.

---

## ⚡ Automated Setup

The easiest way to set up ShareX is to run the automated setup command:

```bash
screen-ai --setup-sharex
```

### What `--setup-sharex` does:
1. **Verifies Engine & Models:** Checks if ScreenAI library and model files are present. If missing, it downloads the latest binaries from Google CIPD automatically.
2. **Locates ShareX Config:** Finds `HotkeysConfig.json` in your Windows `Documents/ShareX` folder.
3. **Adds/Updates Hotkey:** Configures a custom action mapped to **`Ctrl + Shift + O`**:
   - Executes: `screen-ai ocr "$input" --sharex`
   - Capture Mode: Rectangle Light
4. **Safely Restarts ShareX:** Safely closes ShareX to write changes without file locking issues, then restarts ShareX.

---

## 📋 Manual Setup

If you prefer to configure ShareX manually:

1. Open ShareX -> **Hotkey settings...**
2. Click **Add...**
3. Set **Task**: `Capture region`
4. Check **Override after capture tasks**: Enable `Save image to file` and `Perform actions`
5. Go to **Actions** settings in ShareX:
   - **Name**: `Google ScreenAI OCR`
   - **File path**: Path to `screen-ai` (or `python.exe`)
   - **Arguments**: `ocr "$input" --sharex`
   - Check **Hidden window**
