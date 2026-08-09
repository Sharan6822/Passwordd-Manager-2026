import time
import tkinter as tk
from typing import Optional, List, Dict
from core.crypto import is_vault_initialized
from core.vault import load_vault
from core.config import load_settings
from core.logger import log_activity

from ui.setup_frame import SetupFrame
from ui.login_frame import LoginFrame
from ui.sidebar import SidebarFrame
from ui.dashboard_frame import DashboardFrame
from ui.vault_frame import VaultFrame
from ui.generator_frame import GeneratorFrame
from ui.history_frame import HistoryFrame
from ui.csv_frame import CSVFrame
from ui.breach_frame import BreachFrame
from ui.settings_frame import SettingsFrame

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Offline Password Manager")
        self.geometry("1080x700")
        self.minsize(920, 580)
        self.configure(bg=BG_COLOR)

        self.key: Optional[bytes] = None
        self.entries: List[Dict] = []
        self.settings: dict = load_settings()

        self.last_activity_time = time.time()
        self.is_locked = True
        self.current_route = "dashboard"

        self.bind_all("<Key>", self._on_user_activity)
        self.bind_all("<Button>", self._on_user_activity)
        self.bind_all("<Motion>", self._on_user_activity)

        self.setup_frame: Optional[SetupFrame] = None
        self.login_frame: Optional[LoginFrame] = None
        self.sidebar_frame: Optional[SidebarFrame] = None
        self.top_header: Optional[tk.Frame] = None
        self.content_container: Optional[tk.Frame] = None

        self.views: dict = {}

        self.after(5000, self._check_inactivity_loop)
        self._init_screen()

    def _on_user_activity(self, event=None):
        self.last_activity_time = time.time()

    def _check_inactivity_loop(self):
        if not self.is_locked and self.key:
            lock_minutes = self.settings.get("auto_lock_minutes", 5)
            idle_seconds = time.time() - self.last_activity_time
            if idle_seconds >= (lock_minutes * 60):
                log_activity("AUTO_LOCK_TRIGGERED", f"Vault locked after {lock_minutes} mins inactivity.")
                self.lock_vault()
        self.after(5000, self._check_inactivity_loop)

    def _init_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        if not is_vault_initialized():
            self.setup_frame = SetupFrame(self, on_setup_complete=self.on_unlocked)
            self.setup_frame.pack(fill="both", expand=True)
        else:
            self.login_frame = LoginFrame(self, on_login_success=self.on_unlocked, on_reset_vault=self.reset_vault)
            self.login_frame.pack(fill="both", expand=True)

    def reset_vault(self):
        from core import config
        for f in [config.SALT_FILE, config.VERIFY_FILE, config.VAULT_FILE, config.WORDS_FILE]:
            if f.exists():
                try:
                    f.unlink()
                except Exception as e:
                    print(f"Error removing {f}: {e}")
        self.key = None
        self.is_locked = True
        self._init_screen()

    def on_unlocked(self, key: bytes):
        self.key = key
        self.is_locked = False
        self.last_activity_time = time.time()

        try:
            self.entries = load_vault(self.key)
        except Exception as e:
            self.entries = []
            log_activity("VAULT_LOAD_ERROR", str(e))

        for widget in self.winfo_children():
            widget.destroy()

        self.top_header = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1, height=42)
        self.top_header.pack(fill="x", side="top")
        self.top_header.pack_propagate(False)

        tk.Label(
            self.top_header,
            text="● VAULT UNLOCKED  |  AES-128 ENCRYPTED",
            font=("Consolas", 9, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(side="left", padx=16)

        lock_btn = tk.Button(
            self.top_header,
            text="🔒 Lock Now",
            font=("Segoe UI", 9, "bold"),
            bg="#1d202a",
            fg="#f0f2f5",
            activebackground="#2a2e3d",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.lock_vault
        )
        lock_btn.pack(side="right", padx=14)

        body = tk.Frame(self, bg=BG_COLOR)
        body.pack(fill="both", expand=True)

        self.sidebar_frame = SidebarFrame(
            body,
            on_navigate=self.navigate_to,
            on_lock=self.lock_vault
        )
        self.sidebar_frame.pack(side="left", fill="y")

        self.content_container = tk.Frame(body, bg=BG_COLOR)
        self.content_container.pack(side="right", fill="both", expand=True)

        self.views["dashboard"] = DashboardFrame(
            self.content_container,
            entries=self.entries,
            nav_callback=self.navigate_to,
            lock_callback=self.lock_vault
        )

        self.views["vault"] = VaultFrame(
            self.content_container,
            entries=self.entries,
            key=self.key,
            copy_callback=self.copy_to_clipboard,
            on_vault_changed=self._reload_vault_data
        )

        self.views["generator"] = GeneratorFrame(
            self.content_container,
            key=self.key,
            copy_callback=self.copy_to_clipboard,
            nav_callback=self.navigate_to
        )

        self.views["history"] = HistoryFrame(
            self.content_container,
            key=self.key,
            copy_callback=self.copy_to_clipboard
        )

        self.views["csv"] = CSVFrame(
            self.content_container,
            entries=self.entries,
            key=self.key,
            on_vault_changed=self._reload_vault_data
        )

        self.views["breach"] = BreachFrame(self.content_container)

        self.views["settings"] = SettingsFrame(
            self.content_container,
            on_settings_changed=self._reload_settings
        )

        self.navigate_to("dashboard")

    def navigate_to(self, route: str):
        if route == "vault_add":
            route = "vault"
            self.sidebar_frame.set_active("vault")
            self.views["vault"].open_entry_modal(None)

        self.current_route = route
        for view_name, view_obj in self.views.items():
            if view_name == route:
                view_obj.pack(fill="both", expand=True)
                if route == "history" and hasattr(view_obj, "refresh_history"):
                    view_obj.refresh_history()
                elif route == "dashboard" and hasattr(view_obj, "update_data"):
                    view_obj.update_data(self.entries)
            else:
                view_obj.pack_forget()

    def _reload_vault_data(self):
        if self.key:
            self.entries = load_vault(self.key)
            if "dashboard" in self.views:
                self.views["dashboard"].update_data(self.entries)
            if "vault" in self.views:
                self.views["vault"].update_data(self.entries, self.key)
            if "csv" in self.views:
                self.views["csv"].update_data(self.entries, self.key)

    def _reload_settings(self):
        self.settings = load_settings()

    def copy_to_clipboard(self, text: str):
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

        log_activity("CLIPBOARD_COPY", "Copied credential to clipboard.")

        clear_secs = self.settings.get("clipboard_clear_seconds", 20)
        self.after(clear_secs * 1000, lambda t=text: self._safe_clear_clipboard(t))

    def _safe_clear_clipboard(self, target_text: str):
        try:
            current_clip = self.clipboard_get()
            if current_clip == target_text:
                self.clipboard_clear()
                log_activity("CLIPBOARD_CLEAR", "Auto-cleared sensitive clipboard data.")
        except Exception:
            pass

    def lock_vault(self):
        self.key = None
        self.entries = []
        self.is_locked = True
        self.views = {}
        log_activity("VAULT_LOCKED", "Vault locked by user action.")
        self._init_screen()
