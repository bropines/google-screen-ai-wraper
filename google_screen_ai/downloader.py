import os
import sys
import platform
import logging
import urllib.request
import tempfile
import subprocess
from pathlib import Path
from typing import Union

logger = logging.getLogger("google_screen_ai.downloader")

CIPD_PACKAGE = "chromium/third_party/screen-ai"
CIPD_URL_TEMPLATE = "https://chrome-infra-packages.appspot.com/client?platform={platform}&version={version}"

def get_cipd_platform() -> str:
    """Detect and return the platform name matching Google's CIPD registry."""
    os_name = platform.system().lower()
    arch = platform.machine().lower()
    
    if os_name == "darwin":
        os_name = "mac"
    elif os_name == "windows":
        os_name = "windows"
        
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "x86": "386",
        "i386": "386",
        "i686": "386"
    }
    cipd_arch = arch_map.get(arch, arch)
    return f"{os_name}-{cipd_arch}"

def get_binary_name() -> str:
    """Return the name of the dynamic library on the current OS."""
    if sys.platform == "win32":
        return "chrome_screen_ai.dll"
    # Both Linux and macOS use libchromescreenai.so in Google's builds
    return "libchromescreenai.so"

def get_default_model_dir() -> Path:
    """Get the default cross-platform model directory (in ~/.config/screen_ai)."""
    return Path.home() / ".config" / "screen_ai"

def is_installed(model_dir: Union[str, Path]) -> bool:
    """Check if ScreenAI library is already installed in the given directory."""
    path = Path(model_dir)
    lib_path = path / "resources" / get_binary_name()
    return lib_path.exists()

def download_screen_ai(model_dir: Union[str, Path] = None, force: bool = False) -> bool:
    """
    Downloads and extracts the ScreenAI binaries and models using the CIPD tool.
    
    Args:
        model_dir: The directory to export models to (e.g. ~/.config/screen_ai).
                   If None, uses the default ~/.config/screen_ai.
        force: If True, re-downloads even if the library is already present.
    """
    if model_dir is None:
        model_dir = get_default_model_dir()
        
    model_dir = Path(model_dir)
    
    if not force and is_installed(model_dir):
        logger.info(f"ScreenAI is already installed at {model_dir}")
        return True

    cipd_platform = get_cipd_platform()
    package_name = f"{CIPD_PACKAGE}/{cipd_platform}"
    ensure_content = f"{package_name} latest\n"
    
    logger.info(f"Downloading ScreenAI models for {cipd_platform}...")
    logger.info(f"Target directory: {model_dir.resolve()}")

    # Ensure parent directory exists
    model_dir.mkdir(parents=True, exist_ok=True)
    
    cipd_bin = "cipd.exe" if sys.platform == "win32" else "cipd"
    cipd_url = CIPD_URL_TEMPLATE.format(platform=cipd_platform, version="latest")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        cipd_path = Path(tmp_dir) / cipd_bin
        
        # 1. Download CIPD client
        try:
            logger.debug(f"Downloading CIPD client from {cipd_url}...")
            urllib.request.urlretrieve(cipd_url, cipd_path)
            if sys.platform != "win32":
                os.chmod(cipd_path, 0o755)
        except Exception as e:
            logger.error(f"Failed to download CIPD client: {e}")
            return False
            
        # 2. Run CIPD client to export ScreenAI
        # Use CREATE_NO_WINDOW on Windows to prevent console flashing in GUI apps
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        cmd = [str(cipd_path), "export", "-root", str(model_dir), "-ensure-file", "-"]
        
        try:
            logger.debug(f"Running CIPD export for {package_name}...")
            result = subprocess.run(
                cmd,
                input=ensure_content,
                text=True,
                check=True,
                capture_output=True,
                creationflags=flags
            )
            logger.info("ScreenAI files successfully downloaded and extracted.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"CIPD export failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error executing CIPD export: {e}")
            return False
