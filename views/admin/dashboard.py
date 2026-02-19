"""
管理者ダッシュボード（タブで機能切り替え）
"""
import tkinter as tk
from tkinter import ttk
from views.styles import apply_theme, BG, PRIMARY, FONT_TITLE, FONT_NORMAL, CARD_BG


class AdminDashboard:
    def __init__(self, root: tk.Toplevel, parent: tk.Tk):
        self.root = root
        self.root.title("管理者モード")
        self.root.geometry("1100x720")
        self.root.resizable(True, True)
        self.root.configure(bg=BG)

        self._build()

    def _build(self):
        # ヘッダー
        header = tk.Frame(self.root, bg=PRIMARY, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚙️  管理者ダッシュボード", font=FONT_TITLE,
                 bg=PRIMARY, fg="white").pack(side="left", padx=20, pady=10)

        # タブ
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        # アンケート管理タブ
        from views.admin.survey_manager import SurveyManagerTab
        tab1 = ttk.Frame(nb, style="TFrame")
        nb.add(tab1, text="  📋 アンケート管理  ")
        SurveyManagerTab(tab1)

        # ユーザー管理タブ
        from views.admin.user_manager import UserManagerTab
        tab2 = ttk.Frame(nb, style="TFrame")
        nb.add(tab2, text="  👤 職員マスター管理  ")
        UserManagerTab(tab2)

        # 集計・グラフタブ
        from views.admin.aggregator import AggregatorTab
        tab3 = ttk.Frame(nb, style="TFrame")
        nb.add(tab3, text="  📊 集計・グラフ  ")
        AggregatorTab(tab3)

        # アクセスログタブ
        from views.admin.access_log_tab import AccessLogTab
        tab4 = ttk.Frame(nb, style="TFrame")
        nb.add(tab4, text="  🗒️ アクセスログ  ")
        AccessLogTab(tab4)

        # 設定タブ
        from views.admin.settings_tab import SettingsTab
        tab5 = ttk.Frame(nb, style="TFrame")
        nb.add(tab5, text="  ⚙️ 設定  ")
        SettingsTab(tab5)
