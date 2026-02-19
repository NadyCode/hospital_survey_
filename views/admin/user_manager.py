"""
職員マスターデータ管理タブ
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import csv

from config import get_data_path, MASTER_USER_FILE
from models.user import StaffMember, load_master_users, save_master_users
from views.styles import (PRIMARY, DANGER, SUCCESS, BG, CARD_BG, FONT_LARGE, FONT_NORMAL,
                           FONT_MEDIUM, MUTED)


class UserManagerTab:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self.users: list[StaffMember] = []
        self._build()
        self._load()

    def _build(self):
        toolbar = tk.Frame(self.parent, bg=BG, pady=8)
        toolbar.pack(fill="x", padx=16)

        tk.Button(toolbar, text="＋ 職員を追加", font=FONT_NORMAL, bg=SUCCESS, fg="white",
                  relief="flat", padx=10, pady=5, command=self._add).pack(side="left", padx=2)
        tk.Button(toolbar, text="✏️ 編集", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=5, command=self._edit).pack(side="left", padx=2)
        tk.Button(toolbar, text="🗑️ 削除", font=FONT_NORMAL, bg=DANGER, fg="white",
                  relief="flat", padx=10, pady=5, command=self._delete).pack(side="left", padx=2)
        tk.Button(toolbar, text="📂 CSVからインポート", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=5, command=self._import_csv).pack(side="left", padx=8)
        tk.Button(toolbar, text="💾 CSVに保存", font=FONT_NORMAL, bg=PRIMARY, fg="white",
                  relief="flat", padx=10, pady=5, command=self._save).pack(side="right", padx=2)
        tk.Button(toolbar, text="🔄 更新", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=5, command=self._load).pack(side="right", padx=2)

        # フィルター
        filter_frame = tk.Frame(self.parent, bg=BG)
        filter_frame.pack(fill="x", padx=16, pady=(0, 4))
        tk.Label(filter_frame, text="部署で絞り込み:", font=FONT_NORMAL, bg=BG).pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                         font=FONT_NORMAL, width=20, state="readonly")
        self.filter_combo.pack(side="left", padx=4)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_tree())
        tk.Button(filter_frame, text="全表示", font=FONT_NORMAL, relief="flat",
                  command=lambda: [self.filter_var.set(""), self._refresh_tree()]).pack(side="left", padx=4)

        self.count_label = tk.Label(filter_frame, text="", font=FONT_NORMAL, bg=BG, fg=MUTED)
        self.count_label.pack(side="right")

        # ツリービュー
        frame = tk.Frame(self.parent)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        cols = ("部署", "氏名")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=250)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit())

    def _load(self):
        fpath = get_data_path(MASTER_USER_FILE)
        self.users = load_master_users(fpath)
        self._refresh_filter_combo()
        self._refresh_tree()

    def _refresh_filter_combo(self):
        depts = sorted(set(u.department for u in self.users))
        self.filter_combo["values"] = [""] + depts

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        dept_filter = self.filter_var.get()
        displayed = [u for u in self.users if not dept_filter or u.department == dept_filter]
        for u in displayed:
            self.tree.insert("", "end", values=(u.department, u.name))
        self.count_label.config(text=f"{len(displayed)} 名 / 合計 {len(self.users)} 名")

    def _sort(self, col: str):
        key = "department" if col == "部署" else "name"
        self.users.sort(key=lambda u: getattr(u, key))
        self._refresh_tree()

    def _add(self):
        dept = simpledialog.askstring("追加", "部署名を入力:")
        if not dept:
            return
        name = simpledialog.askstring("追加", "氏名を入力:")
        if not name:
            return
        self.users.append(StaffMember(department=dept.strip(), name=name.strip()))
        self._refresh_filter_combo()
        self._refresh_tree()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("選択なし", "編集する行を選択してください")
            return
        values = self.tree.item(sel[0])["values"]
        old_dept, old_name = str(values[0]), str(values[1])

        dept = simpledialog.askstring("編集", "部署名:", initialvalue=old_dept)
        if dept is None:
            return
        name = simpledialog.askstring("編集", "氏名:", initialvalue=old_name)
        if name is None:
            return

        for u in self.users:
            if u.department == old_dept and u.name == old_name:
                u.department = dept.strip()
                u.name = name.strip()
                break
        self._refresh_filter_combo()
        self._refresh_tree()

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("選択なし", "削除する行を選択してください")
            return
        if not messagebox.askyesno("確認", f"{len(sel)} 件を削除しますか？"):
            return
        to_remove = set()
        for item in sel:
            values = self.tree.item(item)["values"]
            to_remove.add((str(values[0]), str(values[1])))
        self.users = [u for u in self.users
                      if (u.department, u.name) not in to_remove]
        self._refresh_filter_combo()
        self._refresh_tree()

    def _save(self):
        fpath = get_data_path(MASTER_USER_FILE)
        save_master_users(fpath, self.users)
        messagebox.showinfo("保存完了", f"職員マスターを保存しました。\n({fpath})")

    def _import_csv(self):
        fpath = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSV ファイル", "*.csv"), ("全ファイル", "*.*")])
        if not fpath:
            return
        try:
            new_users = load_master_users(fpath)
            if not new_users:
                messagebox.showwarning("空", "インポートできるデータがありませんでした。")
                return
            mode = messagebox.askquestion(
                "インポート方法",
                f"{len(new_users)} 件を読み込みました。\n「はい」=上書き、「いいえ」=追記",
                icon="question")
            if mode == "yes":
                self.users = new_users
            else:
                self.users.extend(new_users)
            self._refresh_filter_combo()
            self._refresh_tree()
        except Exception as e:
            messagebox.showerror("インポートエラー", str(e))
