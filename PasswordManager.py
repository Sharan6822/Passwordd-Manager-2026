import sys
import os
import tkinter as tk
from core.config import ensure_directories
from ui.app import MainApp

def main():
    # Ensure portable folder structure exists
    ensure_directories()

    # Enable High DPI awareness on Windows if available
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    # Start main Tkinter Application
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()
