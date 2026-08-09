import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict
from core.generator import load_generator_history, clear_generator_history

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"
ENTRY_BG = "#161822"

class HistoryFrame(tk.Frame):
    def __init__(self, parent, key: bytes, copy_callback: Callable[[str], None]):
        super().__init__(parent, bg=BG_COLOR)
        self.key = key
        self.copy_callback = copy_callback

        self._build_ui()

    def update_key(self, key: bytes):
        self.key = key
        self._refresh_list()

    def refresh_history(self):
        self._refresh_list()

    def _build_ui(self):
        # Header Controls Bar
        top_bar = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            top_bar,
            text="📜 GENERATOR HISTORY",
            font=("Consolas", 14, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(side="left", padx=15, pady=12)

        # Search Entry
        self.search_entry = tk.Entry(
            top_bar,
            font=("Segoe UI", 10),
            bg=ENTRY_BG,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            width=24
        )
        self.search_entry.pack(side="left", padx=10, pady=12, ipady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_list())

        # Clear History Button
        clear_btn = tk.Button(
            top_bar,
            text="🗑️ Clear History",
            font=("Segoe UI", 9, "bold"),
            bg="#2a1a1e",
            fg="#f87171",
            activebackground="#3d2026",
            activeforeground="#ff8888",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._confirm_clear
        )
        clear_btn.pack(side="right", padx=15, pady=12)

        # Scrollable Canvas
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.items_container = tk.Frame(canvas, bg=BG_COLOR)

        self.items_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.items_container, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 15))
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 15))

        self._refresh_list()

    def _refresh_list(self):
        for w in self.items_container.winfo_children():
            w.destroy()

        history = load_generator_history(self.key)
        q = self.search_entry.get().strip().lower()

        if q:
            history = [h for h in history if (q in h.get("password", "").lower() or q in h.get("mode", "").lower() or q in h.get("timestamp", "").lower())]

        if not history:
            tk.Label(
                self.items_container,
                text="No password generator history recorded yet.",
                font=("Segoe UI", 11),
                bg=BG_COLOR,
                fg=TEXT_MUTED
            ).pack(pady=40)
            return

        for record in history:
            card = tk.Frame(self.items_container, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.pack(fill="x", pady=4, padx=5)

            info_frame = tk.Frame(card, bg=CARD_BG)
            info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=8)

            top_row = tk.Frame(info_frame, bg=CARD_BG)
            top_row.pack(anchor="w")

            pw = record.get("password", "")
            mode = record.get("mode", "standard").capitalize()
            ts = record.get("timestamp", "N/A")

            tk.Label(
                top_row,
                text=pw,
                font=("Consolas", 11, "bold"),
                bg=CARD_BG,
                fg="#ffffff"
            ).pack(side="left")

            tk.Label(
                top_row,
                text=f" [{mode}]",
                font=("Segoe UI", 9, "bold"),
                bg=CARD_BG,
                fg=TEXT_MUTED
            ).pack(side="left", padx=10)

            tk.Label(
                info_frame,
                text=f"Generated: {ts}",
                font=("Segoe UI", 8),
                bg=CARD_BG,
                fg=TEXT_MUTED
            ).pack(anchor="w", pady=(2, 0))

            tk.Button(
                card,
                text="📋 Copy",
                font=("Segoe UI", 9, "bold"),
                bg="#2b3040",
                fg="#ffffff",
                activebackground="#3a4157",
                activeforeground="#ffffff",
                relief="flat",
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda p=pw: self.copy_callback(p)
            ).pack(side="right", padx=15, pady=8)

    def _confirm_clear(self):
        dialog = tk.Toplevel(self)
        dialog.title("Clear Generator History")
        dialog.geometry("380x160")
        dialog.configure(bg=BG_COLOR)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="⚠️ CLEAR ALL GENERATOR HISTORY?",
            font=("Segoe UI", 11, "bold"),
            bg=BG_COLOR,
            fg="#f87171"
        ).pack(pady=(20, 10))

        tk.Label(
            dialog,
            text="This will delete all saved generated password records.",
            font=("Segoe UI", 9),
            bg=BG_COLOR,
            fg=TEXT_PRIMARY
        ).pack(pady=(0, 20))

        btn_row = tk.Frame(dialog, bg=BG_COLOR)
        btn_row.pack()

        def do_clear():
            clear_generator_history(self.key)
            dialog.destroy()
            self._refresh_list()

        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg="#1a1d26", fg=TEXT_MUTED, relief="flat", padx=12, pady=5, command=dialog.destroy).pack(side="left", padx=10)
        tk.Button(btn_row, text="Clear", font=("Segoe UI", 9, "bold"), bg="#2a1a1e", fg="#f87171", relief="flat", padx=12, pady=5, command=do_clear).pack(side="left", padx=10)
