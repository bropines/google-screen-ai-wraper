import logging
import platform

logger = logging.getLogger("google_screen_ai.sharex")


def copy_to_clipboard(text: str) -> bool:
    """Copies the provided text to the system clipboard."""
    system = platform.system()
    try:
        import pyperclip

        pyperclip.copy(text)
        logger.info("OCR result text successfully copied to clipboard.")
        return True
    except ImportError:
        logger.error(
            "Module 'pyperclip' not found. Please install it using: pip install google-screen-ai-wraper[clipboard]"
        )
        if system == "Linux":
            logger.info("On Linux, you might also need xclip/xsel: sudo apt-get install xclip")
        return False
    except Exception as e:
        logger.error(f"Failed to copy text to clipboard: {e}")
        return False
