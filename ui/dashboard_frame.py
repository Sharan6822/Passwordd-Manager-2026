import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict
from core.strength import analyze_password

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#ffffff"
TEXT_MUTED = "#e2e8f0"
BTN_BG = "#1d202a"

def _get_white_icon(icon_type: str, size: int = 20):
    if not HAS_PIL:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size, size

    if icon_type == "logo":
        points = [
            (w * 0.5, h * 0.08),
            (w * 0.88, h * 0.22),
            (w * 0.88, h * 0.55),
            (w * 0.5, h * 0.92),
            (w * 0.12, h * 0.55),
            (w * 0.12, h * 0.22),
        ]
        draw.polygon(points, outline="#ffffff", width=2)
        draw.line([(w * 0.35, h * 0.48), (w * 0.48, h * 0.62), (w * 0.68, h * 0.38)], fill="#ffffff", width=2)
    elif icon_type == "key":
        draw.ellipse([w*0.1, h*0.1, w*0.5, h*0.5], outline="#ffffff", width=2)
        draw.line([(w*0.45, h*0.45), (w*0.85, h*0.85)], fill="#ffffff", width=2)
        draw.line([(w*0.65, h*0.65), (w*0.8, h*0.5)], fill="#ffffff", width=2)
        draw.line([(w*0.75, h*0.75), (w*0.9, h*0.6)], fill="#ffffff", width=2)
    elif icon_type == "warning":
        points = [(w*0.5, h*0.1), (w*0.9, h*0.85), (w*0.1, h*0.85)]
        draw.polygon(points, outline="#ffffff", width=2)
        draw.line([(w*0.5, h*0.35), (w*0.5, h*0.6)], fill="#ffffff", width=2)
        draw.ellipse([w*0.46, h*0.7, w*0.54, h*0.78], fill="#ffffff")
    elif icon_type == "sync":
        draw.arc([w*0.15, h*0.15, w*0.85, h*0.85], 220, 40, fill="#ffffff", width=2)
        draw.arc([w*0.15, h*0.15, w*0.85, h*0.85], 40, 220, fill="#ffffff", width=2)
        draw.polygon([(w*0.75, h*0.1), (w*0.9, h*0.25), (w*0.7, h*0.3)], fill="#ffffff")
        draw.polygon([(w*0.25, h*0.9), (w*0.1, h*0.75), (w*0.3, h*0.7)], fill="#ffffff")
    elif icon_type == "shield":
        points = [
            (w * 0.5, h * 0.1),
            (w * 0.85, h * 0.25),
            (w * 0.85, h * 0.55),
            (w * 0.5, h * 0.9),
            (w * 0.15, h * 0.55),
            (w * 0.15, h * 0.25),
        ]
        draw.polygon(points, fill="#ffffff")
    return ImageTk.PhotoImage(img)

class DashboardFrame(tk.Frame):
    def __init__(
        self,
        parent,
        entries: List[Dict],
        nav_callback: Callable[[str], None],
        lock_callback: Callable[[], None]
    ):
        super().__init__(parent, bg=BG_COLOR)
        self.entries = entries
        self.nav_callback = nav_callback
        self.lock_callback = lock_callback
        self.cards = []
        self.action_btns = []
        self.is_compact = False
        self._icon_refs = []

        self._build_ui()
        self.bind("<Configure>", self._on_resize)

    def update_data(self, entries: List[Dict]):
        self.entries = entries
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _on_resize(self, event):
        compact = event.width < 780
        if compact != self.is_compact:
            self.is_compact = compact
            self._regrid_cards()

    def _regrid_cards(self):
        if not self.cards:
            return
        if self.is_compact:
            for idx, card in enumerate(self.cards):
                r, c = divmod(idx, 2)
                card.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
            for idx, btn in enumerate(self.action_btns):
                r, c = divmod(idx, 2)
                btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
        else:
            for idx, card in enumerate(self.cards):
                card.grid(row=0, column=idx, padx=4, pady=0, sticky="ew")
            for idx, btn in enumerate(self.action_btns):
                btn.grid(row=0, column=idx, padx=4, pady=0, sticky="ew")

    def _build_ui(self):
        self.cards = []
        self.action_btns = []

        total_entries = len(self.entries)
        weak_count = 0
        reused_count = 0
        seen_passwords = set()
        reused_passwords = set()

        for entry in self.entries:
            pw = entry.get("password", "")
            if pw:
                if pw in seen_passwords:
                    reused_passwords.add(pw)
                seen_passwords.add(pw)

                res = analyze_password(pw, self.entries, current_entry_id=entry.get("id"))
                if res["score"] < 65:
                    weak_count += 1

        for entry in self.entries:
            pw = entry.get("password", "")
            if pw in reused_passwords:
                reused_count += 1

        # Header Title
        title_box = tk.Frame(self, bg=BG_COLOR)
        title_box.pack(fill="x", padx=22, pady=(18, 10))

        logo_img = _get_white_icon("logo", size=24)
        if logo_img:
            self._icon_refs.append(logo_img)
            logo_lbl = tk.Label(title_box, image=logo_img, bg=BG_COLOR)
            logo_lbl.pack(side="left", padx=(0, 10))
        else:
            logo_lbl = tk.Label(title_box, text="🛡", font=("Segoe UI", 16, "bold"), bg=BG_COLOR, fg="#ffffff")
            logo_lbl.pack(side="left", padx=(0, 10))

        tk.Label(
            title_box,
            text="SECURITY DASHBOARD",
            font=("Consolas", 14, "bold"),
            bg=BG_COLOR,
            fg="#ffffff"
        ).pack(side="left")

        # Stats Cards Grid
        self.stats_frame = tk.Frame(self, bg=BG_COLOR)
        self.stats_frame.pack(fill="x", padx=18, pady=8)
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.cards.append(self._create_card(self.stats_frame, 0, "TOTAL CREDENTIALS", str(total_entries), "key", "🔑"))
        self.cards.append(self._create_card(self.stats_frame, 1, "WEAK PASSWORDS", str(weak_count), "warning", "⚠️"))
        self.cards.append(self._create_card(self.stats_frame, 2, "REUSED PASSWORDS", str(reused_count), "sync", "🔄"))
        self.cards.append(self._create_card(self.stats_frame, 3, "ENCRYPTION MODE", "AES-128", "shield", "🛡️"))

        # Quick Actions Panel
        actions_panel = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        actions_panel.pack(fill="x", padx=22, pady=12)

        tk.Label(
            actions_panel,
            text="QUICK ACTIONS",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#38bdf8",
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 8))

        self.btn_row = tk.Frame(actions_panel, bg=CARD_BG)
        self.btn_row.pack(fill="x", padx=14, pady=(0, 12))
        self.btn_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        actions = [
            ("➕ Add New Item", "vault_add"),
            ("🎲 Password Generator", "generator"),
            ("📁 Import / Export", "csv"),
            ("🛡️ Breach Check", "breach"),
        ]

        for idx, (label, route) in enumerate(actions):
            btn = tk.Button(
                self.btn_row,
                text=label,
                font=("Segoe UI", 9, "bold"),
                bg=BTN_BG,
                fg="#ffffff",
                activebackground="#2a2e3d",
                activeforeground="#ffffff",
                relief="flat",
                pady=8,
                cursor="hand2",
                command=lambda r=route: self.nav_callback(r)
            )
            btn.grid(row=0, column=idx, padx=4, sticky="ew")
            self.action_btns.append(btn)

        # Health Breakdown Box
        health_box = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        health_box.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        tk.Label(
            health_box,
            text="VAULT SECURITY HEALTH SUMMARY",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#38bdf8",
            anchor="w"
        ).pack(fill="x", padx=18, pady=(12, 8))

        canvas = tk.Canvas(health_box, bg=CARD_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(health_box, orient="vertical", command=canvas.yview)
        scroll_health = tk.Frame(canvas, bg=CARD_BG)

        scroll_health.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_health, anchor="nw")

        def _on_health_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_health_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=(0, 12))
        scrollbar.pack(side="right", fill="y", padx=(0, 14), pady=(0, 12))

        if not self.entries:
            tk.Label(
                scroll_health,
                text="No vault entries found. Click 'Add New Item' to store passwords securely.",
                font=("Segoe UI", 9),
                bg=CARD_BG,
                fg=TEXT_MUTED
            ).pack(pady=18)
        else:
            for entry in self.entries:
                pw = entry.get("password", "")
                res = analyze_password(pw, self.entries, current_entry_id=entry.get("id"))

                row_item = tk.Frame(scroll_health, bg="#161822", highlightbackground=BORDER_COLOR, highlightthickness=1)
                row_item.pack(fill="x", pady=2, padx=4)

                tk.Label(
                    row_item,
                    text=f"{entry.get('site_name', 'Unnamed')} ({entry.get('username', 'No User')})",
                    font=("Segoe UI", 9, "bold"),
                    bg="#161822",
                    fg=TEXT_PRIMARY
                ).pack(side="left", padx=12, pady=7)

                tk.Label(
                    row_item,
                    text=f"{res['label']} ({res['score']}/100)",
                    font=("Consolas", 9, "bold"),
                    bg="#161822",
                    fg=res["color"]
                ).pack(side="right", padx=12, pady=7)

    def _create_card(self, parent, col, title, value, icon_type, fallback_emoji):
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.grid(row=0, column=col, padx=4, sticky="ew")

        top_row = tk.Frame(card, bg=CARD_BG)
        top_row.pack(fill="x", padx=10, pady=(8, 0))

        ic_img = _get_white_icon(icon_type, size=18)
        if ic_img:
            self._icon_refs.append(ic_img)
            tk.Label(top_row, image=ic_img, bg=CARD_BG).pack(side="left")
        else:
            tk.Label(top_row, text=fallback_emoji, font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg="#ffffff").pack(side="left")

        tk.Label(top_row, text=title, font=("Segoe UI", 8, "bold"), bg=CARD_BG, fg=TEXT_MUTED).pack(side="right")

        tk.Label(
            card,
            text=value,
            font=("Consolas", 18, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(anchor="w", padx=10, pady=(2, 8))
        return card
