import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict
from core.generator import (
    generate_standard_password, generate_memorable_password,
    load_memorable_words, save_memorable_words, add_generator_history_entry,
    DEFAULT_WORDS
)
from core.strength import analyze_password

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"
ENTRY_BG = "#161822"

class GeneratorFrame(tk.Frame):
    def __init__(
        self,
        parent,
        key: bytes,
        copy_callback: Callable[[str], None],
        nav_callback: Callable[[str], None]
    ):
        super().__init__(parent, bg=BG_COLOR)
        self.key = key
        self.copy_callback = copy_callback
        self.nav_callback = nav_callback

        self.current_mode = "standard"  # "standard" or "memorable"
        self.generated_pw = ""
        self.memorable_words = load_memorable_words(self.key)

        self._build_ui()

    def update_key(self, key: bytes):
        self.key = key
        self.memorable_words = load_memorable_words(self.key)

    def _build_ui(self):
        # Header Controls
        top_bar = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            top_bar,
            text="🎲 PASSWORD GENERATOR",
            font=("Consolas", 14, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(side="left", padx=15, pady=12)

        # Segmented Mode Buttons
        mode_frame = tk.Frame(top_bar, bg=CARD_BG)
        mode_frame.pack(side="right", padx=15, pady=10)

        self.std_btn = tk.Button(
            mode_frame,
            text="Standard Random",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: self._on_mode_change("standard")
        )
        self.std_btn.pack(side="left", padx=2)

        self.mem_btn = tk.Button(
            mode_frame,
            text="Memorable Word-Based",
            font=("Segoe UI", 9, "bold"),
            bg="#1a1d26",
            fg=TEXT_MUTED,
            activebackground="#262a38",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: self._on_mode_change("memorable")
        )
        self.mem_btn.pack(side="left", padx=2)

        # Main Container
        self.main_container = tk.Frame(self, bg=BG_COLOR)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # --- Password Preview Banner ---
        preview_card = tk.Frame(self.main_container, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        preview_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            preview_card,
            text="LIVE PASSWORD PREVIEW",
            font=("Segoe UI", 8, "bold"),
            bg=CARD_BG,
            fg=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(10, 0))

        prev_row = tk.Frame(preview_card, bg=CARD_BG)
        prev_row.pack(fill="x", padx=20, pady=(5, 8))

        self.preview_lbl = tk.Entry(
            prev_row,
            font=("Consolas", 15, "bold"),
            bg=ENTRY_BG,
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.preview_lbl.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=6)

        # Regenerate Button
        tk.Button(
            prev_row,
            text="🔄 Regenerate",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.generate
        ).pack(side="left", padx=3)

        # Copy Button
        tk.Button(
            prev_row,
            text="📋 Copy",
            font=("Segoe UI", 9, "bold"),
            bg="#1a1d26",
            fg=TEXT_PRIMARY,
            activebackground="#262a38",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._copy_generated
        ).pack(side="left", padx=3)

        # Custom Strength Meter Bar
        self.bar_bg = tk.Frame(preview_card, bg="#222634", height=6)
        self.bar_bg.pack(fill="x", padx=20, pady=(0, 5))
        self.bar_fill = tk.Frame(self.bar_bg, bg="#4ade80", height=6, width=0)
        self.bar_fill.pack(side="left", fill="y")

        self.strength_info_lbl = tk.Label(
            preview_card,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG
        )
        self.strength_info_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        # --- Controls Area ---
        self.controls_frame = tk.Frame(self.main_container, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.controls_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Action Buttons Bottom Row
        action_row = tk.Frame(self.main_container, bg=BG_COLOR)
        action_row.pack(fill="x", pady=5)

        self.toast_lbl = tk.Label(action_row, text="", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg="#4ade80")
        self.toast_lbl.pack(side="left")

        tk.Button(
            action_row,
            text="📜 Save to History",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._save_to_history
        ).pack(side="right", padx=5)

        self._render_controls()
        self.generate()

    def _on_mode_change(self, mode: str):
        self.current_mode = mode
        if mode == "standard":
            self.std_btn.config(bg="#2b3040", fg="#ffffff")
            self.mem_btn.config(bg="#1a1d26", fg=TEXT_MUTED)
        else:
            self.mem_btn.config(bg="#2b3040", fg="#ffffff")
            self.std_btn.config(bg="#1a1d26", fg=TEXT_MUTED)
        self._render_controls()
        self.generate()

    def _render_controls(self):
        for w in self.controls_frame.winfo_children():
            w.destroy()

        if self.current_mode == "standard":
            tk.Label(
                self.controls_frame,
                text="⚙️ STANDARD GENERATOR OPTIONS",
                font=("Segoe UI", 11, "bold"),
                bg=CARD_BG,
                fg=TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", padx=20, pady=(15, 10))

            # Length Slider Row
            slider_row = tk.Frame(self.controls_frame, bg=CARD_BG)
            slider_row.pack(fill="x", padx=20, pady=5)

            tk.Label(slider_row, text="Password Length:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED).pack(side="left")
            self.len_lbl = tk.Label(slider_row, text="16 characters", font=("Consolas", 10, "bold"), bg=CARD_BG, fg="#ffffff")
            self.len_lbl.pack(side="left", padx=10)

            self.len_scale = ttk.Scale(
                self.controls_frame,
                from_=8,
                to=64,
                command=self._on_slider_move
            )
            self.len_scale.set(16)
            self.len_scale.pack(fill="x", padx=20, pady=(0, 15))

            chk_frame = tk.Frame(self.controls_frame, bg=CARD_BG)
            chk_frame.pack(fill="x", padx=20, pady=5)

            self.upper_var = tk.BooleanVar(value=True)
            self.lower_var = tk.BooleanVar(value=True)
            self.digit_var = tk.BooleanVar(value=True)
            self.symbol_var = tk.BooleanVar(value=True)
            self.ambig_var = tk.BooleanVar(value=True)

            chks = [
                ("Uppercase (A-Z)", self.upper_var, 0, 0),
                ("Lowercase (a-z)", self.lower_var, 0, 1),
                ("Digits (0-9)", self.digit_var, 1, 0),
                ("Symbols (!@#$)", self.symbol_var, 1, 1),
            ]

            for label, var, r, c in chks:
                cb = tk.Checkbutton(
                    chk_frame,
                    text=label,
                    variable=var,
                    font=("Segoe UI", 9),
                    bg=CARD_BG,
                    fg=TEXT_PRIMARY,
                    selectcolor=BG_COLOR,
                    activebackground=CARD_BG,
                    command=self.generate
                )
                cb.grid(row=r, column=c, padx=10, pady=4, sticky="w")

            tk.Checkbutton(
                chk_frame,
                text="Exclude Ambiguous Chars (l, 1, I, O, 0)",
                variable=self.ambig_var,
                font=("Segoe UI", 9),
                bg=CARD_BG,
                fg=TEXT_PRIMARY,
                selectcolor=BG_COLOR,
                activebackground=CARD_BG,
                command=self.generate
            ).grid(row=2, column=0, columnspan=2, padx=10, pady=4, sticky="w")

        else:
            tk.Label(
                self.controls_frame,
                text="🧠 MEMORABLE WORD GENERATOR OPTIONS",
                font=("Segoe UI", 11, "bold"),
                bg=CARD_BG,
                fg=TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", padx=20, pady=(15, 5))

            tk.Label(
                self.controls_frame,
                text="Generates passwords by combining 2 of your personal encrypted words with random casing,\nseparators, injected digits, and symbols (e.g. Tiger#47-Comet).",
                font=("Segoe UI", 9),
                bg=CARD_BG,
                fg=TEXT_MUTED,
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=20, pady=(0, 15))

            words_info = tk.Frame(self.controls_frame, bg=ENTRY_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
            words_info.pack(fill="x", padx=20, pady=(0, 15))

            tk.Label(words_info, text="Your Encrypted Personal Words Pool:", font=("Segoe UI", 8, "bold"), bg=ENTRY_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=12, pady=(8, 4))
            words_str = ", ".join(self.memorable_words)
            tk.Label(words_info, text=words_str, font=("Consolas", 10), bg=ENTRY_BG, fg="#ffffff", wraplength=550, justify="left", anchor="w").pack(fill="x", padx=12, pady=(0, 8))

            tk.Button(
                self.controls_frame,
                text="✏️ Edit Personal Words",
                font=("Segoe UI", 9, "bold"),
                bg="#1a1d26",
                fg=TEXT_PRIMARY,
                activebackground="#262a38",
                activeforeground="#ffffff",
                relief="flat",
                padx=12,
                pady=6,
                cursor="hand2",
                command=self._open_edit_words_modal
            ).pack(anchor="w", padx=20, pady=(0, 15))

    def _on_slider_move(self, value):
        val = int(float(value))
        if hasattr(self, 'len_lbl'):
            self.len_lbl.config(text=f"{val} characters")
        self.generate()

    def generate(self):
        if self.current_mode == "standard":
            if not hasattr(self, 'len_scale'):
                return
            length = int(float(self.len_scale.get()))
            pw = generate_standard_password(
                length=length,
                use_upper=self.upper_var.get() if hasattr(self, 'upper_var') else True,
                use_lower=self.lower_var.get() if hasattr(self, 'lower_var') else True,
                use_digits=self.digit_var.get() if hasattr(self, 'digit_var') else True,
                use_symbols=self.symbol_var.get() if hasattr(self, 'symbol_var') else True,
                exclude_ambiguous=self.ambig_var.get() if hasattr(self, 'ambig_var') else True
            )
        else:
            pw = generate_memorable_password(self.memorable_words)

        self.generated_pw = pw
        self.preview_lbl.delete(0, 'end')
        self.preview_lbl.insert(0, pw)

        res = analyze_password(pw)
        total_w = self.bar_bg.winfo_width()
        fill_w = int(total_w * (res["score"] / 100.0)) if total_w > 0 else 0
        self.bar_fill.config(width=fill_w, bg=res["color"])
        self.strength_info_lbl.config(
            text=f"Strength: {res['label']} ({res['score']}/100) • Entropy: {res['entropy']} bits",
            fg=res["color"]
        )

    def _copy_generated(self):
        if self.generated_pw:
            self.copy_callback(self.generated_pw)
            self.toast_lbl.config(text="Copied to clipboard!")
            self.after(2500, lambda: self.toast_lbl.config(text=""))

    def _save_to_history(self):
        if self.generated_pw:
            add_generator_history_entry(self.generated_pw, self.current_mode, self.key)
            self.toast_lbl.config(text="✓ Saved to Generator History!")
            self.after(2500, lambda: self.toast_lbl.config(text=""))

    def _open_edit_words_modal(self):
        dialog = tk.Toplevel(self)
        dialog.title("Edit Personal Memorable Words")
        dialog.geometry("440x520")
        dialog.configure(bg=BG_COLOR)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="✏️ EDIT 10 PERSONAL WORDS",
            font=("Consolas", 12, "bold"),
            bg=BG_COLOR,
            fg="#ffffff"
        ).pack(pady=(15, 10))

        bottom_bar = tk.Frame(dialog, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        bottom_bar.pack(side="bottom", fill="x")

        err_lbl = tk.Label(dialog, text="", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg="#f87171")
        err_lbl.pack(side="bottom", pady=(4, 2))

        scroll = tk.Frame(dialog, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        word_entries = []
        for i in range(10):
            row_frame = tk.Frame(scroll, bg=CARD_BG)
            row_frame.pack(fill="x", pady=3, padx=5)

            tk.Label(row_frame, text=f"Word {i+1}:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, width=8, anchor="w").pack(side="left")
            val = self.memorable_words[i] if i < len(self.memorable_words) else ""
            e = tk.Entry(row_frame, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
            e.insert(0, val)
            e.pack(side="left", fill="x", expand=True, ipady=4)
            word_entries.append(e)

        def save_words():
            new_w = [ent.get().strip() for ent in word_entries if ent.get().strip()]
            if len(new_w) < 2:
                err_lbl.config(text="Provide at least 2 non-empty words.")
                return
            save_memorable_words(new_w, self.key)
            self.memorable_words = new_w
            dialog.destroy()
            self._render_controls()

        tk.Button(
            bottom_bar,
            text="Cancel",
            font=("Segoe UI", 9, "bold"),
            bg="#1a1d26",
            fg=TEXT_MUTED,
            activebackground="#262a38",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            command=dialog.destroy
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            bottom_bar,
            text="💾 SAVE WORDS",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            command=save_words
        ).pack(side="right", fill="x", expand=True, padx=(0, 15), pady=10)
