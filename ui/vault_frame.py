import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Optional
from core.vault import (
    filter_entries, add_entry, update_entry, delete_entry,
    get_categories, check_duplicate_passwords
)
from core.strength import analyze_password
from core.generator import generate_standard_password
from core.breach import launch_browser_url

BG_COLOR = "#0a0b0e"
CARD_BG = "#12141a"
BORDER_COLOR = "#1c202b"
TEXT_PRIMARY = "#f0f2f5"
TEXT_MUTED = "#7a8292"
ENTRY_BG = "#161822"

class VaultFrame(tk.Frame):
    def __init__(
        self,
        parent,
        entries: List[Dict],
        key: bytes,
        copy_callback: Callable[[str], None],
        on_vault_changed: Callable[[], None]
    ):
        super().__init__(parent, bg=BG_COLOR)
        self.entries = entries
        self.key = key
        self.copy_callback = copy_callback
        self.on_vault_changed = on_vault_changed

        self.current_category = "All"
        self.search_query = ""

        self._build_ui()

    def update_data(self, entries: List[Dict], key: bytes):
        self.entries = entries
        self.key = key
        self._refresh_list()

    def _build_ui(self):
        # Header Controls Bar
        top_bar = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            top_bar,
            text="🔑 PASSWORD VAULT",
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
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, pady=12, ipady=5)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Category Option Menu dropdown
        categories = ["All"] + get_categories(self.entries)
        self.category_var = tk.StringVar(value="All")
        cat_opt = ttk.OptionMenu(
            top_bar,
            self.category_var,
            "All",
            *categories,
            command=self._on_category_changed
        )
        cat_opt.pack(side="left", padx=5, pady=12)

        # Add Entry Button
        add_btn = tk.Button(
            top_bar,
            text="➕ ADD ENTRY",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.open_entry_modal(None)
        )
        add_btn.pack(side="right", padx=15, pady=12)

        # Interactive Toast Banner
        self.toast_banner = tk.Frame(self, bg=CARD_BG, highlightbackground="#4ade80", highlightthickness=1)
        
        self.toast_msg_lbl = tk.Label(
            self.toast_banner,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#4ade80"
        )
        self.toast_msg_lbl.pack(side="left", padx=15, pady=8)

        self.toast_pass_btn = tk.Button(
            self.toast_banner,
            text="🔑 Step 2: Copy Password Now",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2"
        )
        self.toast_pass_btn.pack(side="right", padx=15, pady=8)

        # Scrollable Vault Item List Container
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.items_container = tk.Frame(canvas, bg=BG_COLOR)

        self.items_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.items_container, anchor="nw")
        
        def _on_items_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_items_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 15))
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 15))

        self._refresh_list()

    def _on_search_changed(self, event=None):
        self.search_query = self.search_entry.get()
        self._refresh_list()

    def _on_category_changed(self, choice: str):
        self.current_category = choice
        self._refresh_list()

    def _refresh_list(self):
        for w in self.items_container.winfo_children():
            w.destroy()

        filtered = filter_entries(self.entries, self.search_query, self.current_category)

        if not filtered:
            tk.Label(
                self.items_container,
                text="No vault entries match your filter or vault is empty.",
                font=("Segoe UI", 11),
                bg=BG_COLOR,
                fg=TEXT_MUTED
            ).pack(pady=40)
            return

        for entry in filtered:
            self._render_entry_card(entry)

    def _launch_site_and_copy_user(self, entry: Dict):
        url = entry.get("url", "").strip()
        username = entry.get("username", "").strip()
        password = entry.get("password", "")
        site_name = entry.get("site_name", "Site")

        if username:
            self.copy_callback(username)
            user_msg = f"Copied username ('{username}') to clipboard!"
        else:
            user_msg = "No username stored."

        if url:
            launch_browser_url(url, in_private=False)
            banner_text = f"🚀 Step 1: Opened {site_name} in standard browser & {user_msg}"
        else:
            banner_text = f"📋 Step 1: {user_msg}"

        self.toast_banner.pack(fill="x", padx=20, pady=(0, 10))
        self.toast_msg_lbl.config(text=banner_text)

        def copy_pass_action():
            if password:
                self.copy_callback(password)
                self.toast_msg_lbl.config(text=f"✓ Step 2 Complete: Password copied for {site_name}!")
                self.after(5000, self.toast_banner.pack_forget)
            else:
                self.toast_msg_lbl.config(text="No password set for this entry.")

        self.toast_pass_btn.config(command=copy_pass_action)

    def _render_entry_card(self, entry: Dict):
        card = tk.Frame(self.items_container, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.pack(fill="x", pady=4, padx=5)

        info_frame = tk.Frame(card, bg=CARD_BG)
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=8)

        top_info = tk.Frame(info_frame, bg=CARD_BG)
        top_info.pack(anchor="w")

        tk.Label(
            top_info,
            text=entry.get("site_name", "Unnamed"),
            font=("Segoe UI", 11, "bold"),
            bg=CARD_BG,
            fg=TEXT_PRIMARY
        ).pack(side="left")

        tk.Label(
            top_info,
            text=f" [{entry.get('category', 'General')}]",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#828a9c"
        ).pack(side="left", padx=5)

        user_val = entry.get('username', 'N/A')
        url_val = entry.get('url', '').strip()

        sub_info = tk.Frame(info_frame, bg=CARD_BG)
        sub_info.pack(anchor="w", pady=(2, 0))

        tk.Label(
            sub_info,
            text=f"User: {user_val}",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED
        ).pack(side="left")

        if url_val:
            tk.Label(sub_info, text=" • ", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED).pack(side="left")
            url_btn = tk.Label(
                sub_info,
                text=f"🌐 {url_val}",
                font=("Segoe UI", 9, "underline"),
                bg=CARD_BG,
                fg="#e2e8f0",
                cursor="hand2"
            )
            url_btn.pack(side="left")
            url_btn.bind("<Button-1>", lambda e, ent=entry: self._launch_site_and_copy_user(ent))

        pw = entry.get("password", "")
        res = analyze_password(pw, self.entries, current_entry_id=entry.get("id"))
        dups = check_duplicate_passwords(self.entries, pw, current_entry_id=entry.get("id"))

        badges_frame = tk.Frame(card, bg=CARD_BG)
        badges_frame.pack(side="left", padx=10)

        tk.Label(
            badges_frame,
            text=f"Strength: {res['label']}",
            font=("Segoe UI", 8, "bold"),
            bg=CARD_BG,
            fg=res["color"]
        ).pack(anchor="e")

        if dups:
            tk.Label(
                badges_frame,
                text="⚠️ REUSED PASSWORD",
                font=("Segoe UI", 8, "bold"),
                bg=CARD_BG,
                fg="#fbbf24"
            ).pack(anchor="e")

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.pack(side="right", padx=12, pady=8)

        # Action Buttons
        tk.Button(
            btn_frame,
            text="🚀 Open & User",
            font=("Segoe UI", 9, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=lambda e=entry: self._launch_site_and_copy_user(e)
        ).pack(side="left", padx=2)

        tk.Button(
            btn_frame,
            text="📋 Copy Pass",
            font=("Segoe UI", 9),
            bg="#1a1d26",
            fg=TEXT_PRIMARY,
            activebackground="#262a38",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=lambda p=pw: self.copy_callback(p)
        ).pack(side="left", padx=2)

        tk.Button(
            btn_frame,
            text="✏️ Edit",
            font=("Segoe UI", 9),
            bg="#1a1d26",
            fg=TEXT_PRIMARY,
            activebackground="#262a38",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=lambda e=entry: self.open_entry_modal(e)
        ).pack(side="left", padx=2)

        tk.Button(
            btn_frame,
            text="🗑️",
            font=("Segoe UI", 9),
            bg="#2a1a1e",
            fg="#f87171",
            activebackground="#3d2026",
            activeforeground="#ff8888",
            relief="flat",
            padx=6,
            pady=4,
            cursor="hand2",
            command=lambda e=entry: self._confirm_delete(e)
        ).pack(side="left", padx=2)

    def open_entry_modal(self, existing_entry: Optional[Dict] = None):
        dialog = tk.Toplevel(self)
        dialog.title("Edit Vault Entry" if existing_entry else "Add New Vault Entry")
        dialog.geometry("520x640")
        dialog.configure(bg=BG_COLOR)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="✏️ EDIT VAULT ENTRY" if existing_entry else "➕ ADD NEW VAULT ENTRY",
            font=("Consolas", 14, "bold"),
            bg=BG_COLOR,
            fg="#ffffff"
        ).pack(pady=(15, 10))

        bottom_bar = tk.Frame(dialog, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        bottom_bar.pack(side="bottom", fill="x")

        err_lbl = tk.Label(dialog, text="", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg="#f87171")
        err_lbl.pack(side="bottom", pady=(4, 2))

        form_scroll = tk.Frame(dialog, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        form_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        # Site Name
        tk.Label(form_scroll, text="Site / Application Name *", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(15, 2))
        site_ent = tk.Entry(form_scroll, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        site_ent.pack(fill="x", padx=15, pady=(0, 10), ipady=5)
        if existing_entry:
            site_ent.insert(0, existing_entry.get("site_name", ""))

        # URL
        tk.Label(form_scroll, text="URL / Website Address", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(0, 2))
        url_ent = tk.Entry(form_scroll, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        url_ent.pack(fill="x", padx=15, pady=(0, 10), ipady=5)
        if existing_entry:
            url_ent.insert(0, existing_entry.get("url", ""))

        # Username / Email
        tk.Label(form_scroll, text="Username / Email", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(0, 2))
        user_ent = tk.Entry(form_scroll, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        user_ent.pack(fill="x", padx=15, pady=(0, 10), ipady=5)
        if existing_entry:
            user_ent.insert(0, existing_entry.get("username", ""))

        # Password Row
        tk.Label(form_scroll, text="Password *", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(0, 2))
        pw_row = tk.Frame(form_scroll, bg=CARD_BG)
        pw_row.pack(fill="x", padx=15, pady=(0, 5))

        show_var = tk.BooleanVar(value=False)
        pw_ent = tk.Entry(pw_row, show="•", font=("Consolas", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        pw_ent.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=5)
        if existing_entry:
            pw_ent.insert(0, existing_entry.get("password", ""))

        def toggle_show():
            pw_ent.config(show="" if show_var.get() else "•")

        tk.Checkbutton(pw_row, text="Show", variable=show_var, command=toggle_show, font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_PRIMARY, selectcolor=BG_COLOR, activebackground=CARD_BG).pack(side="left", padx=2)

        def fill_generated():
            gen_pw = generate_standard_password(16)
            pw_ent.delete(0, 'end')
            pw_ent.insert(0, gen_pw)
            update_modal_strength()

        tk.Button(pw_row, text="🎲 Gen", font=("Segoe UI", 8, "bold"), bg="#1a1d26", fg=TEXT_PRIMARY, activebackground="#262a38", activeforeground="#ffffff", relief="flat", padx=6, pady=3, command=fill_generated).pack(side="left", padx=2)

        # Modal Strength Bar
        m_bar_bg = tk.Frame(form_scroll, bg="#222634", height=6)
        m_bar_bg.pack(fill="x", padx=15, pady=(2, 2))
        m_bar_fill = tk.Frame(m_bar_bg, bg="#f87171", height=6, width=0)
        m_bar_fill.pack(side="left", fill="y")
        m_lbl = tk.Label(form_scroll, text="", font=("Segoe UI", 8, "bold"), bg=CARD_BG)
        m_lbl.pack(anchor="w", padx=15, pady=(0, 8))

        def update_modal_strength(event=None):
            p = pw_ent.get()
            r = analyze_password(p, self.entries, current_entry_id=existing_entry.get("id") if existing_entry else None)
            total_w = m_bar_bg.winfo_width()
            fill_w = int(total_w * (r["score"] / 100.0)) if total_w > 0 else 0
            m_bar_fill.config(width=fill_w, bg=r["color"])
            m_lbl.config(text=f"Strength: {r['label']} ({r['score']}/100)", fg=r["color"])

        pw_ent.bind("<KeyRelease>", update_modal_strength)
        update_modal_strength()

        # Category Tag
        tk.Label(form_scroll, text="Category Tag", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(5, 2))
        cats = get_categories(self.entries)
        cat_var = tk.StringVar(value=existing_entry.get("category", "General") if existing_entry else "General")
        cat_opt = ttk.OptionMenu(form_scroll, cat_var, cat_var.get(), *cats)
        cat_opt.pack(fill="x", padx=15, pady=(0, 10))

        # Notes
        tk.Label(form_scroll, text="Notes", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=15, pady=(0, 2))
        notes_ent = tk.Entry(form_scroll, font=("Segoe UI", 10), bg=ENTRY_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1)
        notes_ent.pack(fill="x", padx=15, pady=(0, 15), ipady=5)
        if existing_entry:
            notes_ent.insert(0, existing_entry.get("notes", ""))

        def save_action():
            s_name = site_ent.get().strip()
            p_val = pw_ent.get()
            if not s_name:
                err_lbl.config(text="Site/App name is required.")
                return
            if not p_val:
                err_lbl.config(text="Password field cannot be empty.")
                return

            data = {
                "site_name": s_name,
                "url": url_ent.get().strip(),
                "username": user_ent.get().strip(),
                "password": p_val,
                "category": cat_var.get().strip(),
                "notes": notes_ent.get().strip()
            }

            if existing_entry:
                update_entry(self.entries, existing_entry["id"], data, self.key)
            else:
                add_entry(self.entries, data, self.key)

            dialog.destroy()
            self.on_vault_changed()

        tk.Button(
            bottom_bar,
            text="Cancel",
            font=("Segoe UI", 9, "bold"),
            bg="#1a1d26",
            fg=TEXT_MUTED,
            activebackground="#262a38",
            activeforeground="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
            command=dialog.destroy
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            bottom_bar,
            text="💾 SAVE ENTRY",
            font=("Segoe UI", 10, "bold"),
            bg="#2b3040",
            fg="#ffffff",
            activebackground="#3a4157",
            activeforeground="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
            command=save_action
        ).pack(side="right", fill="x", expand=True, padx=(0, 15), pady=10)

    def _confirm_delete(self, entry: Dict):
        dialog = tk.Toplevel(self)
        dialog.title("Confirm Delete")
        dialog.geometry("380x180")
        dialog.configure(bg=BG_COLOR)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="⚠️ DELETE ENTRY?",
            font=("Segoe UI", 12, "bold"),
            bg=BG_COLOR,
            fg="#f87171"
        ).pack(pady=(20, 10))

        tk.Label(
            dialog,
            text=f"Are you sure you want to delete '{entry.get('site_name')}'?\nThis action cannot be undone.",
            font=("Segoe UI", 9),
            bg=BG_COLOR,
            fg=TEXT_PRIMARY,
            justify="center"
        ).pack(pady=(0, 20))

        btn_row = tk.Frame(dialog, bg=BG_COLOR)
        btn_row.pack()

        def do_delete():
            delete_entry(self.entries, entry["id"], self.key)
            dialog.destroy()
            self.on_vault_changed()

        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg="#1a1d26", fg=TEXT_MUTED, relief="flat", padx=12, pady=5, command=dialog.destroy).pack(side="left", padx=10)
        tk.Button(btn_row, text="Delete", font=("Segoe UI", 9, "bold"), bg="#2a1a1e", fg="#f87171", relief="flat", padx=12, pady=5, command=do_delete).pack(side="left", padx=10)
