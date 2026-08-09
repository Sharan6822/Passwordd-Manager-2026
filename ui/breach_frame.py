import tkinter as tk
from tkinter import ttk
from core.breach import BREACH_SERVICES, launch_breach_check_url

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"

class BreachFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)

        self._build_ui()

    def _build_ui(self):
        # Header Controls Bar
        top_bar = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            top_bar,
            text="🛡️ BREACH & LEAK CHECKER",
            font=("Consolas", 14, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(side="left", padx=15, pady=12)

        # Status / Security Banner
        sec_banner = tk.Frame(self, bg=CARD_BG, highlightbackground="#4ade80", highlightthickness=1)
        sec_banner.pack(fill="x", padx=20, pady=10)

        tk.Label(
            sec_banner,
            text="🔒 OFFLINE-SAFE BROWSER LAUNCHPAD",
            font=("Segoe UI", 11, "bold"),
            bg=CARD_BG,
            fg="#4ade80",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(12, 4))

        tk.Label(
            sec_banner,
            text="This application makes ZERO outbound network calls itself.\nClicking any check button launches Microsoft Edge/Chrome exclusively in InPrivate / Incognito Mode.\nNo passwords or email addresses are ever auto-filled or transmitted by Python.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 12))

        # Status message label
        self.status_lbl = tk.Label(self, text="", font=("Segoe UI", 9, "bold"), bg=BG_COLOR)
        self.status_lbl.pack(pady=5)

        # Scrollable Cards Grid
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll = tk.Frame(canvas, bg=BG_COLOR)

        scroll.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 15))
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 15))

        for service in BREACH_SERVICES:
            card = tk.Frame(scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.pack(fill="x", pady=6, padx=5)

            left_info = tk.Frame(card, bg=CARD_BG)
            left_info.pack(side="left", fill="x", expand=True, padx=20, pady=12)

            tk.Label(
                left_info,
                text=f"🌐 {service['name']}",
                font=("Segoe UI", 11, "bold"),
                bg=CARD_BG,
                fg="#ffffff",
                anchor="w"
            ).pack(fill="x")

            tk.Label(
                left_info,
                text=service["description"],
                font=("Segoe UI", 9),
                bg=CARD_BG,
                fg=TEXT_MUTED,
                anchor="w"
            ).pack(fill="x", pady=(2, 4))

            tk.Label(
                left_info,
                text=f"URL: {service['url']}",
                font=("Consolas", 8),
                bg=CARD_BG,
                fg=TEXT_MUTED,
                anchor="w"
            ).pack(fill="x")

            tk.Button(
                card,
                text="🚀 Launch InPrivate Mode",
                font=("Segoe UI", 9, "bold"),
                bg="#2b3040",
                fg="#ffffff",
                activebackground="#3a4157",
                activeforeground="#ffffff",
                relief="flat",
                padx=12,
                pady=8,
                cursor="hand2",
                command=lambda u=service['url']: self._launch_url(u)
            ).pack(side="right", padx=20, pady=12)

    def _launch_url(self, url: str):
        success, msg = launch_breach_check_url(url)
        if success:
            self.status_lbl.config(text=f"✓ {msg}", fg="#4ade80")
        else:
            self.status_lbl.config(text=f"❌ {msg}", fg="#f87171")
