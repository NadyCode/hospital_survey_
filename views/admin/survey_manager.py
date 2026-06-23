"""
アンケート管理タブ：一覧表示、作成・編集・削除
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import uuid

from config import get_surveys_dir, get_shared_folder
from models.survey import Survey
from views.styles import (PRIMARY, DANGER, SUCCESS, BG, CARD_BG, FONT_LARGE, FONT_NORMAL,
                           FONT_MEDIUM, MUTED, BORDER)
from utils.data_manager import load_answers


class SurveyManagerTab:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self._build()
        self._load_surveys()

    def _build(self):
        toolbar = tk.Frame(self.parent, bg=BG, pady=8)
        toolbar.pack(fill="x", padx=16)

        tk.Button(toolbar, text="＋ 新規アンケート作成", font=FONT_MEDIUM,
                  bg=SUCCESS, fg="white", relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self._new_survey).pack(side="left", padx=(0, 8))
        tk.Button(toolbar, text="✏️ 編集", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=6, cursor="hand2", command=self._edit_selected).pack(side="left", padx=4)
        tk.Button(toolbar, text="📊 集計を見る", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=6, cursor="hand2", command=self._view_results).pack(side="left", padx=4)
        tk.Button(toolbar, text="📦 アーカイブ", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=6, cursor="hand2",
                  command=lambda: self._set_archive(True)).pack(side="left", padx=4)
        tk.Button(toolbar, text="📤 アーカイブ解除", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=6, cursor="hand2",
                  command=lambda: self._set_archive(False)).pack(side="left", padx=4)
        tk.Button(toolbar, text="🗑️ 削除", font=FONT_NORMAL, bg=DANGER, fg="white",
                  relief="flat", padx=10, pady=6, cursor="hand2",
                  command=self._delete_selected).pack(side="left", padx=4)
        tk.Button(toolbar, text="🔄 更新", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=6, cursor="hand2", command=self._load_surveys).pack(side="right")

        # フィルター
        filter_bar = tk.Frame(self.parent, bg=BG)
        filter_bar.pack(fill="x", padx=16, pady=(0, 4))
        self.show_archived_var = tk.BooleanVar(value=False)
        tk.Checkbutton(filter_bar, text="アーカイブしたアンケートも表示する",
                       variable=self.show_archived_var, font=FONT_NORMAL, bg=BG,
                       command=self._load_surveys).pack(side="left")

        # ツリービュー
        cols = ("タイトル", "設問数", "回答数", "種別", "状態", "ファイル名")
        self.tree = ttk.Treeview(self.parent, columns=cols, show="headings", height=18)
        widths = [260, 60, 60, 90, 90, 180]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if w < 180 else "w")
        self.tree.column("タイトル", anchor="w")

        self.tree.tag_configure("archived", foreground=MUTED, background="#F0F0F0")

        scroll = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 8), side="left")
        scroll.pack(side="right", fill="y", pady=(0, 8))

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

    def _load_surveys(self):
        self.tree.delete(*self.tree.get_children())
        show_archived = self.show_archived_var.get()
        survey_dir = get_surveys_dir()
        for fname in sorted(os.listdir(survey_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(survey_dir, fname)
            try:
                s = Survey.load(fpath)
                if s.is_archived and not show_archived:
                    continue
                answers = load_answers(get_shared_folder(), s.id)
                if s.is_test_mode and s.is_anonymous:
                    mode = "匿名テスト"
                elif s.is_test_mode:
                    mode = "テスト"
                elif s.is_anonymous:
                    mode = "匿名"
                else:
                    mode = "通常"
                status = "アーカイブ" if s.is_archived else "アクティブ"
                tags = ("archived",) if s.is_archived else ()
                self.tree.insert("", "end", iid=fname, tags=tags,
                                 values=(s.title, len(s.questions), len(answers),
                                         mode, status, fname))
            except Exception:
                pass

    def _selected_fname(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("選択なし", "アンケートを選択してください")
            return None
        return sel[0]

    def _check_survey_password(self, survey: Survey) -> bool:
        """パスワードが設定されている場合は入力を求める。OKなら True を返す。"""
        if not survey.survey_password:
            return True
        pw = simpledialog.askstring(
            "パスワード確認",
            f"「{survey.title}」のパスワードを入力してください:",
            show="*")
        if pw is None:
            return False
        if pw != survey.survey_password:
            messagebox.showerror("エラー", "パスワードが違います。")
            return False
        return True

    def _new_survey(self):
        sid = str(uuid.uuid4())[:8]
        survey = Survey(id=sid, title="新しいアンケート")
        fpath = os.path.join(get_surveys_dir(), f"survey_{sid}.json")
        survey.save(fpath)
        self._open_editor(survey, fpath)

    def _edit_selected(self):
        fname = self._selected_fname()
        if not fname:
            return
        fpath = os.path.join(get_surveys_dir(), fname)
        try:
            survey = Survey.load(fpath)
        except Exception as e:
            messagebox.showerror("エラー", f"読み込みエラー: {e}")
            return
        if not self._check_survey_password(survey):
            return
        self._open_editor(survey, fpath)

    def _open_editor(self, survey: Survey, fpath: str):
        from views.admin.survey_editor import SurveyEditorWindow
        win = tk.Toplevel(self.parent)
        def on_close():
            self._load_surveys()
            win.destroy()
        SurveyEditorWindow(win, survey, fpath, on_close_callback=on_close)

    def _view_results(self):
        fname = self._selected_fname()
        if not fname:
            return
        fpath = os.path.join(get_surveys_dir(), fname)
        try:
            survey = Survey.load(fpath)
        except Exception as e:
            messagebox.showerror("エラー", str(e))
            return
        if not self._check_survey_password(survey):
            return
        from views.admin.aggregator import AggregatorWindow
        win = tk.Toplevel(self.parent)
        AggregatorWindow(win, survey)

    def _set_archive(self, archived: bool):
        fname = self._selected_fname()
        if not fname:
            return
        fpath = os.path.join(get_surveys_dir(), fname)
        try:
            survey = Survey.load(fpath)
            if survey.is_archived == archived:
                state = "アーカイブ済み" if archived else "アクティブ"
                messagebox.showinfo("情報", f"このアンケートはすでに{state}です。")
                return
            survey.is_archived = archived
            survey.save(fpath)
            action = "アーカイブしました（回答者一覧から非表示になります）" if archived \
                else "アーカイブを解除しました（回答者一覧に再表示されます）"
            self._load_surveys()
            messagebox.showinfo("完了", f"「{survey.title}」を{action}。")
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def _delete_selected(self):
        fname = self._selected_fname()
        if not fname:
            return
        if not messagebox.askyesno("確認", f"「{fname}」を削除しますか？\n回答データは残ります。"):
            return
        fpath = os.path.join(get_surveys_dir(), fname)
        try:
            os.remove(fpath)
            self._load_surveys()
        except Exception as e:
            messagebox.showerror("エラー", str(e))
