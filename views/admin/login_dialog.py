"""
管理者ログインダイアログ
"""
import tkinter as tk
from tkinter import messagebox
from config import get_admin_password
from views.styles import PRIMARY, CARD_BG, FONT_LARGE, FONT_NORMAL, BG


class AdminLoginDialog:
    def __init__(self, parent: tk.Misc):
        self.authenticated = False
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("管理者認証")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=CARD_BG)
        self.dialog.grab_set()

        # ウィンドウを中央に配置
        self.dialog.geometry("360x260")
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 360) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 260) // 2
        self.dialog.geometry(f"360x260+{x}+{y}")

        self._build()
        self.dialog.bind("<Return>", lambda e: self._login())

    def _build(self):
        pad = dict(padx=30)

        tk.Label(self.dialog, text="🔒 管理者ログイン", font=FONT_LARGE,
                 bg=CARD_BG, fg=PRIMARY).pack(pady=(28, 16))

        tk.Label(self.dialog, text="管理者パスワードを入力してください",
                 font=FONT_NORMAL, bg=CARD_BG).pack(**pad)

        self.pw_var = tk.StringVar()
        pw_entry = tk.Entry(self.dialog, textvariable=self.pw_var, show="●",
                            font=FONT_NORMAL, width=24, relief="solid", bd=1)
        pw_entry.pack(pady=12, **pad, ipady=6)
        pw_entry.focus_set()

        self.error_label = tk.Label(self.dialog, text="", fg="red", bg=CARD_BG, font=FONT_NORMAL)
        self.error_label.pack()

        btn_frame = tk.Frame(self.dialog, bg=CARD_BG)
        btn_frame.pack(pady=14)

        tk.Button(btn_frame, text="ログイン", font=FONT_NORMAL, bg=PRIMARY, fg="white",
                  relief="flat", padx=16, pady=6, command=self._login).pack(side="left", padx=6)
        tk.Button(btn_frame, text="キャンセル", font=FONT_NORMAL, relief="flat",
                  padx=16, pady=6, command=self.dialog.destroy).pack(side="left", padx=6)

    def _login(self):
        entered = self.pw_var.get()
        if entered == get_admin_password():
            self.authenticated = True
            self.dialog.destroy()
        else:
            self.error_label.config(text="パスワードが正しくありません")
            self.pw_var.set("")
