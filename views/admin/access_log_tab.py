"""
アクセスログ表示タブ
"""
import tkinter as tk
from tkinter import ttk

from config import get_data_path, ACCESS_LOG_FILE
from utils.logger import read_access_logs
from views.styles import BG, PRIMARY, FONT_NORMAL, FONT_H2, MUTED


class AccessLogTab:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self._build()
        self._load()

    def _build(self):
        toolbar = tk.Frame(self.parent, bg=BG, pady=8)
        toolbar.pack(fill="x", padx=12)
        tk.Label(toolbar, text="端末アクセスログ", font=FONT_H2, bg=BG, fg=PRIMARY).pack(side="left")
        tk.Button(toolbar, text="🔄 更新", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=4, command=self._load).pack(side="right")

        frame = tk.Frame(self.parent)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        cols = ("日時", "端末名", "IPアドレス", "モード", "備考")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        widths = [160, 160, 120, 100, 200]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        logs = read_access_logs(get_data_path(ACCESS_LOG_FILE))
        # 新しい順に表示
        for log in reversed(logs):
            self.tree.insert("", "end", values=(
                log.get("日時", ""), log.get("端末名", ""),
                log.get("IPアドレス", ""), log.get("モード", ""), log.get("備考", "")))
