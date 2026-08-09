import math
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
from core.crypto import verify_master_password
from core.logger import log_activity

BG_COLOR = "#08090d"
CARD_BG = "#0d1117"
BORDER_COLOR = "#00f0ff"
TEXT_PRIMARY = "#ffffff"
TEXT_MUTED = "#cbd5e1"
ENTRY_BG = "#161b26"

class LoginFrame(tk.Frame):
    def __init__(self, parent, on_login_success: Callable[[bytes], None], on_reset_vault: Optional[Callable[[], None]] = None):
        super().__init__(parent, bg=BG_COLOR)
        self.on_login_success = on_login_success
        self.on_reset_vault = on_reset_vault
        self.anim_angle = 0
        self.is_verifying = False

        # Outer Center Card (Sci-Fi Cyber Panel)
        card = tk.Frame(self, bg=CARD_BG, highlightbackground="#00f0ff", highlightthickness=1, width=440)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Inner border accent
        inner_frame = tk.Frame(card, bg=CARD_BG, highlightbackground="#1e293b", highlightthickness=1)
        inner_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Sci-Fi Hologram Core Canvas
        self.canvas = tk.Canvas(inner_frame, width=100, height=100, bg=CARD_BG, highlightthickness=0)
        self.canvas.pack(pady=(20, 5))

        tk.Label(
            inner_frame,
            text="[ SYSTEM GATEWAY ]",
            font=("Consolas", 14, "bold"),
            bg=CARD_BG,
            fg="#00f0ff"
        ).pack(pady=(0, 2))

        tk.Label(
            inner_frame,
            text="PORTABLE VAULT SECURITY",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg="#ffffff"
        ).pack(pady=(0, 2))

        tk.Label(
            inner_frame,
            text="● CLASSIFIED ENCRYPTION // AES-256",
            font=("Consolas", 8, "bold"),
            bg=CARD_BG,
            fg="#4ade80"
        ).pack(pady=(0, 20))

        # Password Entry Box
        self.pw_entry = tk.Entry(
            inner_frame,
            show="•",
            font=("Consolas", 13),
            bg=ENTRY_BG,
            fg="#ffffff",
            insertbackground="#00f0ff",
            relief="flat",
            highlightbackground="#00f0ff",
            highlightthickness=1,
            width=30
        )
        self.pw_entry.pack(pady=(0, 10), ipady=7)
        self.pw_entry.bind("<Return>", lambda e: self._attempt_unlock())
        self.pw_entry.focus()

        # Feedback Label
        self.error_label = tk.Label(
            inner_frame,
            text="",
            font=("Consolas", 9, "bold"),
            bg=CARD_BG,
            fg="#f87171"
        )
        self.error_label.pack(pady=(0, 8))

        # Unlock Button
        self.unlock_btn = tk.Button(
            inner_frame,
            text="[ INITIALIZE SYSTEM ACCESS ]",
            font=("Segoe UI", 10, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            width=32,
            pady=10,
            cursor="hand2",
            command=self._attempt_unlock
        )
        self.unlock_btn.pack(pady=(0, 12))

        # Reset Master Password Option
        reset_btn = tk.Label(
            inner_frame,
            text="[ RE-INITIALIZE MASTER KEY ]",
            font=("Consolas", 9, "underline"),
            bg=CARD_BG,
            fg="#7dd3fc",
            cursor="hand2"
        )
        reset_btn.pack(pady=(0, 22))
        reset_btn.bind("<Button-1>", lambda e: self._prompt_reset_vault())

        # Start animation loop
        self._animate_sci_fi_core()

    def _animate_sci_fi_core(self):
        if not self.winfo_exists():
            return
        self.canvas.delete("all")
        cx, cy = 50, 50
        r_outer = 38
        r_inner = 25

        # Outer ring
        self.canvas.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer, outline="#1e293b", width=2)
        
        # Rotating neon dot
        rad = math.radians(self.anim_angle)
        x_dot = cx + r_outer * math.cos(rad)
        y_dot = cy + r_outer * math.sin(rad)
        self.canvas.create_oval(x_dot - 4, y_dot - 4, x_dot + 4, y_dot + 4, fill="#00f0ff", outline="")

        # Rotating arc segment
        rad2 = math.radians((self.anim_angle + 180) % 360)
        x_dot2 = cx + r_outer * math.cos(rad2)
        y_dot2 = cy + r_outer * math.sin(rad2)
        self.canvas.create_oval(x_dot2 - 3, y_dot2 - 3, x_dot2 + 3, y_dot2 + 3, fill="#38bdf8", outline="")

        # Inner Glowing Core
        self.canvas.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner, fill="#162032", outline="#00f0ff", width=2)

        # Shield polygon
        pts = [cx, cy - 12, cx + 11, cy - 5, cx + 11, cy + 5, cx, cy + 14, cx - 11, cy + 5, cx - 11, cy - 5]
        self.canvas.create_polygon(pts, fill="#00f0ff", outline="")

        self.anim_angle = (self.anim_angle + 6) % 360
        self.after(40, self._animate_sci_fi_core)

    def _attempt_unlock(self):
        if self.is_verifying:
            return
        pw = self.pw_entry.get()
        if not pw:
            self.error_label.config(text="[ ERROR: ENTER MASTER PASSWORD ]", fg="#f87171")
            return

        self.is_verifying = True
        self.error_label.config(text="[ VERIFYING BIOMETRIC KEY... ]", fg="#38bdf8")
        self.unlock_btn.config(state="disabled", bg="#1e293b")

        def _step_verify():
            key = verify_master_password(pw)
            if key:
                self.error_label.config(text="[ ACCESS GRANTED // DECRYPTING ]", fg="#4ade80")
                def _complete():
                    self.pw_entry.delete(0, 'end')
                    log_activity("VAULT_UNLOCK_SUCCESS", "Vault unlocked successfully.")
                    self.is_verifying = False
                    self.unlock_btn.config(state="normal", bg="#0284c7")
                    self.on_login_success(key)
                self.after(200, _complete)
            else:
                self.error_label.config(text="[ ACCESS DENIED // INVALID KEY ]", fg="#f87171")
                log_activity("VAULT_UNLOCK_FAILED", "Invalid master password attempt.")
                self.is_verifying = False
                self.unlock_btn.config(state="normal", bg="#0284c7")

        self.after(200, _step_verify)

    def _prompt_reset_vault(self):
        if messagebox.askyesno(
            "Reset Master Password",
            "Resetting the vault will clear the master password and existing vault data so you can set a new master password.\n\nDo you want to proceed?"
        ):
            if self.on_reset_vault:
                self.on_reset_vault()
