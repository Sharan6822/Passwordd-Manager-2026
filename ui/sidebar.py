import tkinter as tk
from typing import Callable, Dict

BG_COLOR = "#0f1117"
BTN_BG_DEFAULT = "#0f1117"
BTN_FG_DEFAULT = "#cbd5e1"
BTN_BG_HOVER = "#181b24"
BTN_BG_ACTIVE = "#222634"
BTN_FG_ACTIVE = "#ffffff"
BORDER_COLOR = "#1c202b"

class SidebarFrame(tk.Frame):
    def __init__(self, parent, on_navigate: Callable[[str], None], on_lock: Callable[[], None]):
        super().__init__(parent, bg=BG_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1, width=210)
        self.pack_propagate(False)

        self.on_navigate = on_navigate
        self.on_lock = on_lock

        self.buttons: Dict[str, tk.Frame] = {}
        self.button_labels: Dict[str, tk.Label] = {}
        self.active_route = "dashboard"

        self._build_ui()

    def _build_ui(self):
        title_box = tk.Frame(self, bg=BG_COLOR)
        title_box.pack(fill="x", padx=16, pady=(18, 18))

        tk.Label(title_box, text="VAULT MANAGER", font=("Consolas", 13, "bold"), bg=BG_COLOR, fg="#ffffff", anchor="w").pack(fill="x")
        tk.Label(title_box, text="Offline & Portable", font=("Segoe UI", 8, "bold"), bg=BG_COLOR, fg="#38bdf8", anchor="w").pack(fill="x", pady=(2, 0))

        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("vault", "🔑  Password Vault"),
            ("generator", "🎲  Generator"),
            ("history", "📜  History Log"),
            ("csv", "📁  Import / Export"),
            ("breach", "🛡️  Breach Check"),
            ("settings", "⚙️  Settings")
        ]

        nav_container = tk.Frame(self, bg=BG_COLOR)
        nav_container.pack(fill="x", padx=8)

        for route, label_text in nav_items:
            item_frame = tk.Frame(nav_container, bg=BTN_BG_DEFAULT, cursor="hand2")
            item_frame.pack(fill="x", pady=1)

            indicator = tk.Frame(item_frame, bg=BTN_BG_DEFAULT, width=3)
            indicator.pack(side="left", fill="y")

            lbl = tk.Label(
                item_frame, text=label_text, font=("Segoe UI", 9, "bold"),
                bg=BTN_BG_DEFAULT, fg=BTN_FG_DEFAULT, anchor="w", padx=10, pady=8, cursor="hand2"
            )
            lbl.pack(side="left", fill="x", expand=True)

            self.buttons[route] = item_frame
            self.button_labels[route] = lbl

            for widget in (item_frame, lbl, indicator):
                widget.bind("<Button-1>", lambda e, r=route: self.set_active(r))
                widget.bind("<Enter>", lambda e, r=route: self._on_hover(r, True))
                widget.bind("<Leave>", lambda e, r=route: self._on_hover(r, False))

        tk.Frame(self, bg=BG_COLOR).pack(fill="both", expand=True)

        lock_btn = tk.Label(
            self, text="🔒 Lock Vault", font=("Segoe UI", 9, "bold"),
            bg="#181b24", fg="#f0f2f5", activebackground="#222634", activeforeground="#ffffff",
            padx=10, pady=8, cursor="hand2", relief="flat"
        )
        lock_btn.pack(fill="x", padx=10, pady=(0, 10))
        lock_btn.bind("<Button-1>", lambda e: self.on_lock())

        status_box = tk.Frame(self, bg="#12151d", highlightbackground=BORDER_COLOR, highlightthickness=1)
        status_box.pack(fill="x", padx=10, pady=(0, 14))
        tk.Label(status_box, text="● OFFLINE SECURE", font=("Consolas", 8, "bold"), bg="#12151d", fg="#a0a8b8").pack(pady=6)

        self.set_active("dashboard")

    def _on_hover(self, route: str, entering: bool):
        if route == self.active_route:
            return
        bg = BTN_BG_HOVER if entering else BTN_BG_DEFAULT
        fg = "#d0d7de" if entering else BTN_FG_DEFAULT
        self.buttons[route].config(bg=bg)
        self.button_labels[route].config(bg=bg, fg=fg)
        self.buttons[route].winfo_children()[0].config(bg=bg)

    def set_active(self, route: str):
        self.active_route = route
        for r, frame in self.buttons.items():
            lbl = self.button_labels[r]
            ind = frame.winfo_children()[0]
            if r == route:
                frame.config(bg=BTN_BG_ACTIVE)
                lbl.config(bg=BTN_BG_ACTIVE, fg=BTN_FG_ACTIVE)
                ind.config(bg="#ffffff")
            else:
                frame.config(bg=BTN_BG_DEFAULT)
                lbl.config(bg=BTN_BG_DEFAULT, fg=BTN_FG_DEFAULT)
                ind.config(bg=BTN_BG_DEFAULT)
        self.on_navigate(route)
