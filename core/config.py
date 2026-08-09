import os
import sys
import json
from pathlib import Path

def get_app_root() -> Path:
    """
    Returns the absolute Path of the application root directory.
    Supports standard execution and PyInstaller packaged execution.
    All data is kept strictly inside this folder for 100% portability.
    """
    if getattr(sys, 'frozen', False):
        # Executable directory when frozen with PyInstaller
        return Path(sys.executable).parent.resolve()
    else:
        # Source directory
        return Path(__file__).parent.parent.resolve()

APP_ROOT = get_app_root()

# Portable folder paths
DATA_DIR = APP_ROOT / "data"
HISTORY_DIR = APP_ROOT / "history"
EXPORTS_DIR = APP_ROOT / "exports"
LOGS_DIR = APP_ROOT / "logs"

SETTINGS_FILE = DATA_DIR / "settings.json"
SALT_FILE = DATA_DIR / "salt.bin"
VAULT_FILE = DATA_DIR / "vault.enc"
WORDS_FILE = DATA_DIR / "memorable_words.enc"
VERIFY_FILE = DATA_DIR / "verify.bin"
HISTORY_FILE = HISTORY_DIR / "generator_history.enc"
COMMON_PASSWORDS_FILE = DATA_DIR / "common_passwords.txt"
LOG_FILE = LOGS_DIR / "activity.log"

DEFAULT_SETTINGS = {
    "auto_lock_minutes": 5,
    "clipboard_clear_seconds": 20,
    "theme": "dark",
    "edge_path": "",
    "secure_import_delete": True
}

def ensure_directories():
    """Ensure all required portable directories exist within APP_ROOT."""
    for folder in [DATA_DIR, HISTORY_DIR, EXPORTS_DIR, LOGS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

def load_settings() -> dict:
    """Load settings from settings.json or return defaults."""
    ensure_directories()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings = DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception:
            return DEFAULT_SETTINGS.copy()
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    """Save settings dictionary to settings.json."""
    ensure_directories()
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")
