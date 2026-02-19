"""
アプリ設定タブ
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import config
from views.styles import (PRIMARY, BG, CARD_BG, FONT_LARGE, FONT_NORMAL, FONT_MEDIUM, MUTED, SUCCESS)


class SettingsTab:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self._build()

    def _build(self):
        frame = tk.Frame(self.parent, bg=BG)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="アプリケーション設定", font=FONT_LARGE, bg=BG, fg=PRIMARY).pack(anchor="w", pady=(0, 16))

        card = tk.Frame(frame, bg=CARD_BG, relief="ridge", bd=1, padx=20, pady=16)
        card.pack(fill="x")

        def row(parent, label, row_idx):
            tk.Label(parent, text=label, font=FONT_NORMAL, bg=CARD_BG, width=20, anchor="w").grid(
                row=row_idx, column=0, sticky="w", pady=6)

        row(card, "アプリタイトル:", 0)
        self.title_var = tk.StringVar(value=config.APP_CONFIG.get("app_title", ""))
        tk.Entry(card, textvariable=self.title_var, font=FONT_NORMAL, width=36,
                 relief="solid", bd=1).grid(row=0, column=1, sticky="ew", pady=6, padx=8)

        row(card, "共有フォルダパス:", 1)
        folder_frame = tk.Frame(card, bg=CARD_BG)
        folder_frame.grid(row=1, column=1, sticky="ew", pady=6, padx=8)
        self.folder_var = tk.StringVar(value=config.APP_CONFIG.get("shared_folder", ""))
        tk.Entry(folder_frame, textvariable=self.folder_var, font=FONT_NORMAL, width=30,
                 relief="solid", bd=1).pack(side="left", fill="x", expand=True)
        tk.Button(folder_frame, text="参照…", font=FONT_NORMAL, relief="flat",
                  command=self._browse_folder).pack(side="left", padx=4)

        row(card, "管理者パスワード:", 2)
        self.pw_var = tk.StringVar(value=config.APP_CONFIG.get("admin_password", ""))
        tk.Entry(card, textvariable=self.pw_var, font=FONT_NORMAL, width=20,
                 show="●", relief="solid", bd=1).grid(row=2, column=1, sticky="w", pady=6, padx=8)

        card.columnconfigure(1, weight=1)

        tk.Label(frame, text="※ 共有フォルダパスを変更した場合は、アプリを再起動してください。",
                 font=FONT_NORMAL, bg=BG, fg=MUTED).pack(anchor="w", pady=8)

        tk.Button(frame, text="💾 設定を保存", font=FONT_MEDIUM, bg=SUCCESS, fg="white",
                  relief="flat", padx=16, pady=8, command=self._save).pack(anchor="w")

    def _browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_var.set(path)

    def _save(self):
        config.APP_CONFIG["app_title"] = self.title_var.get().strip()
        config.APP_CONFIG["shared_folder"] = self.folder_var.get().strip()
        config.APP_CONFIG["admin_password"] = self.pw_var.get()
        config.save_config(config.APP_CONFIG)
        messagebox.showinfo("保存完了", "設定を保存しました。\n一部の設定はアプリ再起動後に反映されます。")
