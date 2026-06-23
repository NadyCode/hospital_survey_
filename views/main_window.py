"""
アプリケーションメインウィンドウ（モード選択画面）
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os

from config import APP_CONFIG, get_data_path, get_shared_folder, ensure_shared_folder, ACCESS_LOG_FILE
from utils.logger import write_access_log, get_hostname, get_ip_address
from views.styles import (apply_theme, BG, PRIMARY, CARD_BG, FONT_TITLE, FONT_NORMAL, FONT_MEDIUM,
                           FONT_LARGE, FONT_H2, TEXT, MUTED, BORDER)


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_CONFIG.get("app_title", "病院アンケートシステム"))
        self.root.geometry("800x560")
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        self.root.minsize(700, 480)

        apply_theme(root)
        ensure_shared_folder()

        # アクセスログ（起動時）
        try:
            write_access_log(get_data_path(ACCESS_LOG_FILE), mode="起動", extra="")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # ヘッダー
        header = tk.Frame(self.root, bg=PRIMARY, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text=APP_CONFIG.get("app_title", "病院アンケートシステム"),
                 font=FONT_TITLE, bg=PRIMARY, fg="white").pack(side="left", padx=20, pady=12)

        ver = APP_CONFIG.get("app_version", "1.0.0")
        tk.Label(header, text=f"v{ver}", font=FONT_NORMAL, bg=PRIMARY, fg="#BBDEFB").pack(
            side="right", padx=20)

        # メインコンテンツ
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=40, pady=30)

        tk.Label(main, text="モードを選択してください", font=FONT_H2, bg=BG, fg=TEXT).pack(pady=(0, 20))

        btn_frame = tk.Frame(main, bg=BG)
        btn_frame.pack(fill="x")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        # 回答者モード
        respond_card = tk.Frame(btn_frame, bg=CARD_BG, relief="ridge", bd=1)
        respond_card.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        tk.Label(respond_card, text="📝", font=("Yu Gothic UI", 48), bg=CARD_BG).pack(pady=(24, 8))
        tk.Label(respond_card, text="アンケートに回答する", font=FONT_LARGE, bg=CARD_BG, fg=PRIMARY).pack()
        tk.Label(respond_card, text="アンケートフォームを開きます", font=FONT_NORMAL, bg=CARD_BG,
                 fg=MUTED).pack(pady=6)
        tk.Button(respond_card, text="回答を始める", font=FONT_MEDIUM, bg=PRIMARY, fg="white",
                  activebackground="#0D47A1", relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._open_respondent).pack(pady=(10, 24))

        # 管理者モード
        admin_card = tk.Frame(btn_frame, bg=CARD_BG, relief="ridge", bd=1)
        admin_card.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        tk.Label(admin_card, text="⚙️", font=("Yu Gothic UI", 48), bg=CARD_BG).pack(pady=(24, 8))
        tk.Label(admin_card, text="管理者モード", font=FONT_LARGE, bg=CARD_BG, fg="#6A1B9A").pack()
        tk.Label(admin_card, text="作成・集計・ユーザー管理", font=FONT_NORMAL, bg=CARD_BG, fg=MUTED).pack(pady=6)
        tk.Button(admin_card, text="管理者でログイン", font=FONT_MEDIUM, bg="#6A1B9A", fg="white",
                  activebackground="#4A148C", relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._open_admin).pack(pady=(10, 24))

        # フッター（端末名・IP・保存先などの技術情報は一般画面に表示しない）
        info_frame = tk.Frame(main, bg=BG)
        info_frame.pack(fill="x", pady=(20, 0))
        tk.Label(info_frame, text="ご利用の前にモードを選択してください",
                 font=("Yu Gothic UI", 9), bg=BG, fg=MUTED).pack()

    def _open_respondent(self):
        from views.respondent.survey_form import SurveyListWindow
        win = tk.Toplevel(self.root)
        SurveyListWindow(win, self.root)
        try:
            write_access_log(get_data_path(ACCESS_LOG_FILE), mode="回答者モード")
        except Exception:
            pass

    def _open_admin(self):
        from views.admin.login_dialog import AdminLoginDialog
        dlg = AdminLoginDialog(self.root)
        self.root.wait_window(dlg.dialog)
        if dlg.authenticated:
            from views.admin.dashboard import AdminDashboard
            win = tk.Toplevel(self.root)
            AdminDashboard(win, self.root)
            try:
                write_access_log(get_data_path(ACCESS_LOG_FILE), mode="管理者モード")
            except Exception:
                pass
