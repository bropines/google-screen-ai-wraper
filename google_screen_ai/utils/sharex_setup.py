import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Union

from ..downloader import download_screen_ai, is_installed, get_default_model_dir

logger = logging.getLogger("google_screen_ai.sharex_setup")

# The capture the hotkey starts with. RectangleRegion is in every ShareX
# release; RectangleLight, which this used to name, was removed in ShareX 22.0.
# ShareX loads a job it no longer knows as "None" and saves that back, so the
# hotkey stays listed - as "Not selected" - and does nothing when pressed.
CAPTURE_JOB = "RectangleRegion"


def is_sharex_running() -> bool:
    """Checks if ShareX.exe is currently running."""
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq ShareX.exe", "/NH"]
        ).decode("utf-8", errors="ignore")
        return "ShareX.exe" in output
    except Exception:
        return False


def terminate_sharex():
    """Closes ShareX to prevent it from overwriting the config on exit."""
    if is_sharex_running():
        print("ShareX is currently running. Closing it to apply config changes...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "ShareX.exe"], capture_output=True)
            time.sleep(1.5)
        except Exception as e:
            print(f"Error closing ShareX: {e}")


def get_sharex_executable_path() -> Optional[Path]:
    """Attempts to find the ShareX.exe location via Windows Registry or standard paths."""
    try:
        import winreg

        key_path = r"Software\ShareX"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            val, _ = winreg.QueryValueEx(key, "InstallLocation")
            path = Path(val) / "ShareX.exe"
            if path.exists():
                return path
    except Exception:
        pass

    common_paths = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "ShareX" / "ShareX.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "ShareX" / "ShareX.exe",
        Path(os.environ.get("LocalAppData", "")) / "ShareX" / "ShareX.exe",
    ]
    for p in common_paths:
        if p.exists():
            return p
    return None


def get_documents_path() -> Path:
    """Finds the actual Documents folder path on Windows, handling relocations."""
    if sys.platform != "win32":
        return Path(os.path.expanduser("~/Documents"))

    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            val, _ = winreg.QueryValueEx(key, "Personal")
            expanded_val = os.path.expandvars(val)
            return Path(expanded_val)
    except Exception as e:
        logger.debug(f"Failed to find Documents folder via registry: {e}")
        return Path(os.path.expanduser("~/Documents"))


def setup_sharex_config(model_dir: Union[str, Path] = None) -> bool:
    """
    Automatically checks binaries, downloads if missing, and configures ShareX
    to use screen-ai for OCR with automatic clipboard copy.
    """
    if sys.platform != "win32":
        print("Error: ShareX setup is only supported on Windows.")
        return False

    # 1. Check installation and binaries first
    if model_dir is None:
        model_dir = get_default_model_dir()
    else:
        model_dir = Path(model_dir)

    print(f"Checking ScreenAI installation at: {model_dir.resolve()}...")
    if not is_installed(model_dir):
        print("ScreenAI binaries not found. Automatically downloading latest ScreenAI models...")
        success = download_screen_ai(model_dir=model_dir)
        if not success:
            print("Error: Failed to download ScreenAI binaries during setup.")
            return False
    else:
        print("ScreenAI binaries and models are present and ready.")

    # 2. Locate HotkeysConfig.json
    documents_dir = get_documents_path()
    sharex_dir = documents_dir / "ShareX"
    config_path = sharex_dir / "HotkeysConfig.json"

    if not config_path.exists():
        print(f"Error: ShareX configuration file not found at: {config_path}")
        print("Please make sure ShareX is installed and has been run at least once.")
        return False

    # 3. Determine executable path
    found_via_which = shutil.which("screen-ai")
    if found_via_which:
        executable_path = str(Path(found_via_which).resolve())
    else:
        se = sys.executable
        if not se.lower().endswith(("python.exe", "pythonw.exe", "python", "pythonw")):
            executable_path = se
        else:
            executable_path = f'"{se}" -m google_screen_ai'

    print(f"Detected ScreenAI CLI path: {executable_path}")

    # 4. Load and modify ShareX config
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading ShareX config: {e}")
        return False

    hotkeys = config.get("Hotkeys", [])
    exists = False

    # Modify existing task if already present
    for hk in hotkeys:
        task = hk.get("TaskSettings", {})
        programs = task.get("ExternalPrograms") or []
        for prog in programs:
            if prog.get("Name") == "screen-ai":
                hk["HotkeyInfo"] = {"Hotkey": "OemQuotes, Control, Shift", "Win": False}
                prog["Path"] = executable_path
                prog["Args"] = 'ocr "$input" --sharex'
                prog["IsActive"] = True
                # Repair the capture too: ShareX 22 loads the old
                # RectangleLight job as "None", and refreshing only the
                # program left a hotkey that captured nothing.
                if task.get("Job") in (None, "", "None", "RectangleLight"):
                    task["Job"] = CAPTURE_JOB
                exists = True
                print("Found existing 'screen-ai' task in ShareX. Updating hotkey to Ctrl + Shift + ' and executable path...")
                break
        if exists:
            break

    if not exists:
        new_entry = {
            "HotkeyInfo": {"Hotkey": "OemQuotes, Control, Shift", "Win": False},
            "TaskSettings": {
                "Description": "Google ScreenAI OCR (screen-ai)",
                "Job": CAPTURE_JOB,
                "UseDefaultAfterCaptureJob": False,
                "AfterCaptureJob": "SaveImageToFile, PerformActions",
                "UseDefaultActions": False,
                "ExternalPrograms": [
                    {
                        "IsActive": True,
                        "Name": "screen-ai",
                        "Path": executable_path,
                        "Args": 'ocr "$input" --sharex',
                        "OutputExtension": "",
                        "Extensions": "",
                        "HiddenWindow": True,
                        "DeleteInputFile": False,
                    }
                ],
            },
        }
        hotkeys.append(new_entry)
        print("Added new 'Ctrl + Shift + '' hotkey action for Google ScreenAI OCR.")

    config["Hotkeys"] = hotkeys

    # 5. Terminate ShareX before saving
    terminate_sharex()

    # 6. Save config and restart
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print("\nSuccess! ShareX configuration updated.")

        sharex_exe = get_sharex_executable_path()
        if sharex_exe:
            print(f"Opening ShareX from: {sharex_exe}...")
            if sys.platform == "win32":
                os.startfile(str(sharex_exe))
            else:
                subprocess.Popen([str(sharex_exe)])
        else:
            print("ShareX executable not automatically found. Please start ShareX manually.")

        print("\nDefault Hotkey: Ctrl + Shift + ' (Region Capture -> ScreenAI OCR -> Clipboard)")
        return True
    except Exception as e:
        print(f"Error saving ShareX config: {e}")
        return False
