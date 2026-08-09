import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Callable
from core.config import load_settings, save_settings, LOG_FILE
from core.breach import find_edge_executable

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"
ENTRY_BG = "#161822"

class SettingsFrame(tk.Frame):
    def __init__(self, parent, on_settings_changed: Callable[[], None]):
        super().__init__(parent, bg=BG_COLOR)
        self.on_settings_changed = on_settings_changed
        self.settings = load_settings()

        self._build_ui()

    def _build_ui(self):
        # Header Controls Bar
        top_bar = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            top_bar,
            text="⚙️ APPLICATION SETTINGS",
            font=("Consolas", 14, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(side="left", padx=15, pady=12)

        # Scrollable Canvas Body
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

        # --- SECTION 1: TIMEOUT PREFERENCES ---
        sec1 = tk.Frame(scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sec1.pack(fill="x", pady=(0, 15))

        tk.Label(sec1, text="⏱️ Security & Auto-Lock Timeouts", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", padx=20, pady=(15, 10))

        # Inactivity Slider
        row1 = tk.Frame(sec1, bg=CARD_BG)
        row1.pack(fill="x", padx=20, pady=5)

        tk.Label(row1, text="Auto-Lock Inactivity Timeout:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED).pack(side="left")
        self.lock_lbl = tk.Label(row1, text=f"{self.settings.get('auto_lock_minutes', 5)} minutes", font=("Consolas", 10, "bold"), bg=CARD_BG, fg="#ffffff")
        self.lock_lbl.pack(side="left", padx=10)

        self.lock_scale = ttk.Scale(
            sec1,
            from_=1,
            to=60,
            command=self._on_lock_slider
        )
        self.lock_scale.set(self.settings.get("auto_lock_minutes", 5))
        self.lock_scale.pack(fill="x", padx=20, pady=(0, 15))

        # Clipboard Clear Slider
        row2 = tk.Frame(sec1, bg=CARD_BG)
        row2.pack(fill="x", padx=20, pady=5)

        tk.Label(row2, text="Clipboard Auto-Clear Delay:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED).pack(side="left")
        self.clip_lbl = tk.Label(row2, text=f"{self.settings.get('clipboard_clear_seconds', 20)} seconds", font=("Consolas", 10, "bold"), bg=CARD_BG, fg="#4ade80")
        self.clip_lbl.pack(side="left", padx=10)

        self.clip_scale = ttk.Scale(
            sec1,
            from_=5,
            to=60,
            command=self._on_clip_slider
        )
        self.clip_scale.set(self.settings.get("clipboard_clear_seconds", 20))
        self.clip_scale.pack(fill="x", padx=20, pady=(0, 20))

        # --- SECTION 2: BROWSER INPRIVATE EXECUTION ---
        sec2 = tk.Frame(scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sec2.pack(fill="x", pady=10)

        tk.Label(sec2, text="🌐 Browser Executable Path (InPrivate Mode)", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", padx=20, pady=(15, 5))

        curr_edge = find_edge_executable() or "Not found"
        tk.Label(sec2, text=f"Detected Browser Path: {curr_edge}", font=("Consolas", 8), bg=CARD_BG, fg=TEXT_MUTED, wraplength=550, anchor="w").pack(fill="x", padx=20, pady=(0, 10))

        edge_row = tk.Frame(sec2, bg=CARD_BG)
        edge_row.pack(fill="x", padx=20, pady=(0, 20))

        self.edge_ent = tk.Entry(edge_row, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.edge_ent.insert(0, self.settings.get("edge_path", ""))
        self.edge_ent.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)

        tk.Button(edge_row, text="Browse...", font=("Segoe UI", 9, "bold"), bg="#1a1d26", fg=TEXT_PRIMARY, activebackground="#262a38", activeforeground="#ffffff", relief="flat", padx=10, pady=5, cursor="hand2", command=self._browse_edge).pack(side="left")

        # --- SECTION 3: AUDIT LOG VIEWER ---
        sec3 = tk.Frame(scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sec3.pack(fill="x", pady=10)

        tk.Label(sec3, text="📜 Security Audit Log (Local Only)", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(sec3, text="View local security log stored in '/logs/activity.log'. Zero external data transmission.", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=20, pady=(0, 10))

        tk.Button(
            sec3,
            text="👁️ View Audit Log",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._open_log_viewer
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Save Settings Button
        self.save_lbl = tk.Label(scroll, text="", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg="#4ade80")
        self.save_lbl.pack(pady=2)

        tk.Button(
            scroll,
            text="SAVE SETTINGS",
            font=("Segoe UI", 10, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=self._save_all
        ).pack(fill="x", pady=(5, 20))

    def _on_lock_slider(self, val):
        v = int(float(val))
        self.lock_lbl.config(text=f"{v} minutes")

    def _on_clip_slider(self, val):
        v = int(float(val))
        self.clip_lbl.config(text=f"{v} seconds")

    def _browse_edge(self):
        p = filedialog.askopenfilename(title="Select msedge.exe or browser executable", filetypes=[("Executables", "*.exe"), ("All Files", "*.*")])
        if p:
            self.edge_ent.delete(0, 'end')
            self.edge_ent.insert(0, p)

    def _save_all(self):
        self.settings["auto_lock_minutes"] = int(float(self.lock_scale.get()))
        self.settings["clipboard_clear_seconds"] = int(float(self.clip_scale.get()))
        self.settings["edge_path"] = self.edge_ent.get().strip()

        save_settings(self.settings)
        self.save_lbl.config(text="✓ Settings saved successfully!")
        self.after(2500, lambda: self.save_lbl.config(text=""))
        self.on_settings_changed()

    def _open_log_viewer(self):
        dialog = tk.Toplevel(self)
        dialog.title("Local Security Audit Log")
        dialog.geometry("620x420")
        dialog.configure(bg=BG_COLOR)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="📜 LOCAL ACTIVITY LOG (/logs/activity.log)",
            font=("Consolas", 12, "bold"),
            bg=BG_COLOR,
            fg="#ffffff"
        ).pack(pady=(15, 10))

        log_box = tk.Text(dialog, font=("Consolas", 9), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        log_box.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    log_box.insert("1.0", content if content else "Log file is empty.")
            except Exception as e:
                log_box.insert("1.0", f"Error reading log: {e}")
        else:
            log_box.insert("1.0", "Log file does not exist yet.")

        log_box.config(state="disabled")
