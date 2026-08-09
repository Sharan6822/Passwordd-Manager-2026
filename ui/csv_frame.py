import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Callable, List, Dict
from core.config import EXPORTS_DIR
from core.csv_io import export_vault_to_csv, parse_import_csv, secure_delete_file
from core.vault import add_entry, check_duplicate_passwords

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"
ENTRY_BG = "#161822"

class CSVFrame(tk.Frame):
    def __init__(
        self,
        parent,
        entries: List[Dict],
        key: bytes,
        on_vault_changed: Callable[[], None]
    ):
        super().__init__(parent, bg=BG_COLOR)
        self.entries = entries
        self.key = key
        self.on_vault_changed = on_vault_changed

        self.import_filepath: Path = None
        self.parsed_import_entries: List[Dict] = []

        self._build_ui()

    def update_data(self, entries: List[Dict], key: bytes):
        self.entries = entries
        self.key = key

    def _build_ui(self):
        # Header Title
        title_box = tk.Frame(self, bg=BG_COLOR)
        title_box.pack(fill="x", padx=25, pady=(20, 10))

        tk.Label(
            title_box,
            text="📁 CSV IMPORT & EXPORT",
            font=("Consolas", 16, "bold"),
            bg=BG_COLOR,
            fg="#ffffff"
        ).pack(side="left")

        # Scrollable Body Canvas
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

        canvas.pack(side="left", fill="both", expand=True, padx=(25, 0), pady=(0, 20))
        scrollbar.pack(side="right", fill="y", padx=(0, 25), pady=(0, 20))

        # --- SECTION 1: EXPORT VAULT ---
        exp_box = tk.Frame(scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        exp_box.pack(fill="x", pady=(0, 15))

        tk.Label(
            exp_box,
            text="📤 Export Credentials to CSV",
            font=("Segoe UI", 12, "bold"),
            bg=CARD_BG,
            fg="#38bdf8",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(
            exp_box,
            text="Exports your encrypted vault into a standard browser-compatible CSV file. Click EXPORT to choose destination.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg="#cbd5e1",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        exp_form = tk.Frame(exp_box, bg=CARD_BG)
        exp_form.pack(fill="x", padx=20, pady=(0, 15))

        tk.Label(exp_form, text="Format:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg="#e2e8f0").pack(side="left", padx=(0, 5))
        self.exp_fmt_var = tk.StringVar(value="Chrome / Edge Standard")
        exp_fmt_opt = ttk.OptionMenu(exp_form, self.exp_fmt_var, "Chrome / Edge Standard", "Chrome / Edge Standard", "Firefox Standard")
        exp_fmt_opt.pack(side="left", padx=5)

        tk.Label(exp_form, text="Default Filename:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg="#e2e8f0").pack(side="left", padx=(15, 5))
        self.exp_name = tk.Entry(exp_form, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1, width=20)
        self.exp_name.insert(0, "vault_export.csv")
        self.exp_name.pack(side="left", padx=5, ipady=4)

        tk.Button(
            exp_form,
            text="EXPORT...",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self._do_export
        ).pack(side="left", padx=(15, 0))

        self.exp_status = tk.Label(exp_box, text="", font=("Segoe UI", 9, "bold"), bg=CARD_BG)
        self.exp_status.pack(anchor="w", padx=20, pady=(0, 15))

        # --- SECTION 2: IMPORT VAULT ---
        imp_box = tk.Frame(scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        imp_box.pack(fill="x", pady=10)

        tk.Label(
            imp_box,
            text="📥 Import Credentials from CSV",
            font=("Segoe UI", 12, "bold"),
            bg=CARD_BG,
            fg="#38bdf8",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(
            imp_box,
            text="Select a Chrome/Edge/Firefox CSV file. Previews records and checks for duplicate passwords before adding.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg="#cbd5e1",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        imp_row = tk.Frame(imp_box, bg=CARD_BG)
        imp_row.pack(fill="x", padx=20, pady=(0, 10))

        self.file_lbl = tk.Label(imp_row, text="No CSV file selected", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg="#e2e8f0", anchor="w")
        self.file_lbl.pack(side="left", fill="x", expand=True)

        tk.Button(
            imp_row,
            text="Browse CSV...",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._browse_import_file
        ).pack(side="right", padx=5)

        # Pre-import Table Preview Box
        self.preview_frame = tk.Frame(imp_box, bg=ENTRY_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.preview_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(self.preview_frame, text="IMPORT PREVIEW TABLE", font=("Segoe UI", 8, "bold"), bg=ENTRY_BG, fg="#38bdf8", anchor="w").pack(fill="x", padx=15, pady=(10, 5))

        self.preview_scroll = tk.Frame(self.preview_frame, bg=ENTRY_BG)
        self.preview_scroll.pack(fill="x", padx=10, pady=(0, 10))

        # Secure Import Option
        self.sec_del_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            imp_box,
            text="Securely delete source CSV file after successful import (Recommended)",
            variable=self.sec_del_var,
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#4ade80",
            selectcolor=BG_COLOR,
            activebackground=CARD_BG,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(5, 10))

        self.imp_status = tk.Label(imp_box, text="", font=("Segoe UI", 9, "bold"), bg=CARD_BG)
        self.imp_status.pack(anchor="w", padx=20, pady=(0, 5))

        self.commit_btn = tk.Button(
            imp_box,
            text="COMMIT IMPORT TO VAULT",
            font=("Segoe UI", 10, "bold"),
            bg="#1d202a",
            fg="#cbd5e1",
            activebackground="#2a2e3d",
            activeforeground="#ffffff",
            relief="flat",
            state="disabled",
            pady=10,
            cursor="hand2",
            command=self._commit_import
        )
        self.commit_btn.pack(fill="x", padx=20, pady=(5, 20))

    def _do_export(self):
        default_name = self.exp_name.get().strip() or "vault_export.csv"
        if not default_name.endswith(".csv"):
            default_name += ".csv"

        save_path = filedialog.asksaveasfilename(
            initialdir=str(EXPORTS_DIR),
            initialfile=default_name,
            title="Save Exported Credentials CSV File",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not save_path:
            return

        fmt_raw = self.exp_fmt_var.get()
        fmt = "firefox" if "Firefox" in fmt_raw else "chrome"

        try:
            target_path = Path(save_path)
            export_vault_to_csv(self.entries, target_path, format_type=fmt)
            self.exp_name.delete(0, 'end')
            self.exp_name.insert(0, target_path.name)
            self.exp_status.config(text=f"✓ Export successful: Saved to '{target_path.resolve()}'", fg="#4ade80")
        except Exception as e:
            self.exp_status.config(text=f"Export Failed: {str(e)}", fg="#f87171")

    def _browse_import_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=str(EXPORTS_DIR),
            title="Select CSV file to import",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if file_path:
            self.import_filepath = Path(file_path)
            self.file_lbl.config(text=self.import_filepath.name, fg="#ffffff")
            self._load_import_preview()

    def _load_import_preview(self):
        for w in self.preview_scroll.winfo_children():
            w.destroy()

        if not self.import_filepath:
            return

        parsed, errors = parse_import_csv(self.import_filepath)
        self.parsed_import_entries = parsed

        if errors and not parsed:
            self.imp_status.config(text=f"Parse Error: {errors[0]}", fg="#f87171")
            self.commit_btn.config(state="disabled")
            return

        tk.Label(
            self.preview_scroll,
            text=f"Found {len(parsed)} entries to import from CSV:",
            font=("Segoe UI", 9, "bold"),
            bg=ENTRY_BG,
            fg="#4ade80",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        for idx, entry in enumerate(parsed[:30]):
            r_frame = tk.Frame(self.preview_scroll, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
            r_frame.pack(fill="x", pady=2)

            site_txt = f"{idx+1}. {entry['site_name']} ({entry['username']})"
            tk.Label(r_frame, text=site_txt, font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_PRIMARY).pack(side="left", padx=10, pady=4)

            dups = check_duplicate_passwords(self.entries, entry["password"])
            if dups:
                tk.Label(r_frame, text="⚠️ Duplicate Password", font=("Segoe UI", 8, "bold"), bg=CARD_BG, fg="#fbbf24").pack(side="right", padx=10)

        if len(parsed) > 30:
            tk.Label(self.preview_scroll, text=f"... and {len(parsed)-30} more entries.", font=("Segoe UI", 8), bg=ENTRY_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x")

        self.commit_btn.config(state="normal", bg="#2b3040")
        self.imp_status.config(text=f"Ready to import {len(parsed)} entries.", fg="#ffffff")

    def _commit_import(self):
        if not self.parsed_import_entries:
            return

        added_count = 0
        for entry in self.parsed_import_entries:
            add_entry(self.entries, entry, self.key)
            added_count += 1

        del_msg = ""
        if self.sec_del_var.get() and self.import_filepath:
            deleted = secure_delete_file(self.import_filepath)
            if deleted:
                del_msg = " Source CSV securely shredded."

        self.parsed_import_entries = []
        self.commit_btn.config(state="disabled", bg="#1a1d26")
        self.imp_status.config(text=f"✓ Successfully imported {added_count} entries into Vault!{del_msg}", fg="#4ade80")
        self.file_lbl.config(text="No CSV file selected", fg=TEXT_MUTED)

        for w in self.preview_scroll.winfo_children():
            w.destroy()

        self.on_vault_changed()
