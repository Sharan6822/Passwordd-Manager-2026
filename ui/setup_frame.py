import tkinter as tk
from tkinter import ttk
from typing import Callable, List
from core.crypto import setup_master_password
from core.generator import save_memorable_words, DEFAULT_WORDS
from core.strength import analyze_password
from core.vault import create_empty_vault
from core.logger import log_activity

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"
ENTRY_BG = "#161822"

class SetupFrame(tk.Frame):
    def __init__(self, parent, on_setup_complete: Callable[[bytes], None]):
        super().__init__(parent, bg=BG_COLOR)
        self.on_setup_complete = on_setup_complete

        # Scrollable Canvas setup
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_content = tk.Frame(canvas, bg=BG_COLOR)

        self.scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_ui()

    def _build_ui(self):
        content = self.scroll_content

        # Header Title
        tk.Label(
            content,
            text="🛡️ INITIAL VAULT SETUP",
            font=("Consolas", 20, "bold"),
            bg=BG_COLOR,
            fg="#ffffff"
        ).pack(pady=(20, 5))

        tk.Label(
            content,
            text="Set up your master encryption key and personal memorable words.\nAll data is encrypted locally using AES-128-CBC + PBKDF2-HMAC-SHA256.",
            font=("Segoe UI", 10),
            bg=BG_COLOR,
            fg=TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 20))

        # --- Section 1: Master Password ---
        pw_box = tk.Frame(content, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        pw_box.pack(fill="x", pady=10, padx=25)

        tk.Label(
            pw_box,
            text="1. Create Master Password",
            font=("Segoe UI", 12, "bold"),
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(15, 10))

        self.pw_entry = tk.Entry(
            pw_box,
            show="•",
            font=("Consolas", 11),
            bg=ENTRY_BG,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.pw_entry.pack(fill="x", padx=20, pady=5, ipady=6)
        self.pw_entry.bind("<KeyRelease>", self._update_strength_meter)

        self.confirm_entry = tk.Entry(
            pw_box,
            show="•",
            font=("Consolas", 11),
            bg=ENTRY_BG,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.confirm_entry.pack(fill="x", padx=20, pady=5, ipady=6)

        # Custom Strength Bar
        self.bar_bg = tk.Frame(pw_box, bg="#222634", height=8)
        self.bar_bg.pack(fill="x", padx=20, pady=(10, 5))
        self.bar_fill = tk.Frame(self.bar_bg, bg="#ff4d4d", height=8, width=0)
        self.bar_fill.pack(side="left", fill="y")

        self.strength_lbl = tk.Label(
            pw_box,
            text="Strength: Too Weak",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#f87171",
            anchor="w"
        )
        self.strength_lbl.pack(fill="x", padx=20, pady=(0, 15))

        # --- Section 2: 10 Personal Memorable Words ---
        words_box = tk.Frame(content, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        words_box.pack(fill="x", pady=10, padx=25)

        tk.Label(
            words_box,
            text="2. Personal Memorable Words (For Generator)",
            font=("Segoe UI", 12, "bold"),
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(
            words_box,
            text="Enter 10 favorite personal words (hobbies, pets, cities). These are stored ENCRYPTED\nand used to build easy-to-remember passwords.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        grid_frame = tk.Frame(words_box, bg=CARD_BG)
        grid_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.word_entries: List[tk.Entry] = []
        for i in range(10):
            row = i // 2
            col = i % 2
            entry = tk.Entry(
                grid_frame,
                font=("Segoe UI", 10),
                bg=ENTRY_BG,
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
                relief="flat",
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            entry.insert(0, DEFAULT_WORDS[i] if i < len(DEFAULT_WORDS) else "")
            entry.grid(row=row, column=col, padx=6, pady=4, sticky="ew", ipady=5)
            grid_frame.grid_columnconfigure(col, weight=1)
            self.word_entries.append(entry)

        # --- Section 3: Security Warning & Acknowledgment ---
        warn_box = tk.Frame(content, bg="#1a1416", highlightbackground="#4a2228", highlightthickness=1)
        warn_box.pack(fill="x", pady=10, padx=25)

        tk.Label(
            warn_box,
            text="⚠️ NO PASSWORD RECOVERY BY DESIGN",
            font=("Segoe UI", 11, "bold"),
            bg="#1a1416",
            fg="#f87171",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(12, 5))

        tk.Label(
            warn_box,
            text="This application operates 100% offline. There is no cloud, no backdoor, and no recovery mechanism.\nIf you lose your master password, your encrypted vault CANNOT be recovered under any circumstances.",
            font=("Segoe UI", 9),
            bg="#1a1416",
            fg=TEXT_PRIMARY,
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        self.ack_var = tk.BooleanVar(value=False)
        ack_check = tk.Checkbutton(
            warn_box,
            text="I understand that losing my master password permanently locks me out of my vault.",
            variable=self.ack_var,
            font=("Segoe UI", 9, "bold"),
            bg="#1a1416",
            fg="#4ade80",
            activebackground="#1a1416",
            activeforeground="#4ade80",
            selectcolor="#0c0e12",
            anchor="w"
        )
        ack_check.pack(fill="x", padx=20, pady=(0, 15))

        # Status Error Feedback
        self.error_label = tk.Label(content, text="", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg="#f87171")
        self.error_label.pack(pady=5)

        # Complete Setup Button
        setup_btn = tk.Button(
            content,
            text="🔒 INITIALIZE & ENCRYPT VAULT",
            font=("Segoe UI", 11, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            command=self._on_submit
        )
        setup_btn.pack(fill="x", padx=25, pady=(5, 30))

    def _update_strength_meter(self, event=None):
        pw = self.pw_entry.get()
        res = analyze_password(pw)
        score = res["score"]
        
        # Calculate width relative to bar container
        self.update_idletasks()
        total_w = self.bar_bg.winfo_width()
        fill_w = int(total_w * (score / 100.0)) if total_w > 0 else 0
        self.bar_fill.config(width=fill_w, bg=res["color"])
        self.strength_lbl.config(text=f"Strength: {res['label']} ({res['score']}/100)", fg=res["color"])

    def _on_submit(self):
        pw = self.pw_entry.get()
        confirm = self.confirm_entry.get()

        if not pw:
            self.error_label.config(text="Please enter a master password.")
            return
        if len(pw) < 8:
            self.error_label.config(text="Master password must be at least 8 characters long.")
            return
        if pw != confirm:
            self.error_label.config(text="Passwords do not match!")
            return
        if not self.ack_var.get():
            self.error_label.config(text="You must acknowledge the No-Recovery security warning to proceed.")
            return

        words = [e.get().strip() for e in self.word_entries if e.get().strip()]
        if len(words) < 2:
            self.error_label.config(text="Please provide at least 2 personal memorable words.")
            return

        try:
            key = setup_master_password(pw)
            create_empty_vault(key)
            save_memorable_words(words, key)

            log_activity("SETUP_COMPLETE", "Master setup initialized successfully.")
            self.on_setup_complete(key)
        except Exception as e:
            self.error_label.config(text=f"Setup Error: {str(e)}")
