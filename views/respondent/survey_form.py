"""
アンケート回答フォーム（分岐・テスト対応）
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

from config import (get_surveys_dir, get_shared_folder, get_data_path,
                    MASTER_USER_FILE, ACCESS_LOG_FILE)
from models.survey import Survey, Question, QUESTION_TYPES
from models.user import load_master_users, get_departments, get_names_for_department
from utils.data_manager import save_answer, has_answered
from utils.logger import get_hostname, get_ip_address, write_access_log
from views.styles import (PRIMARY, BG, CARD_BG, FONT_LARGE, FONT_NORMAL, FONT_MEDIUM,
                           FONT_H2, FONT_SMALL, MUTED, DANGER, SUCCESS, WARNING,
                           BORDER, TEXT, CORRECT, INCORRECT)


class SurveyListWindow:
    """アンケート選択画面"""
    def __init__(self, root: tk.Toplevel, parent: tk.Tk):
        self.root = root
        root.title("アンケート一覧")
        root.geometry("640x440")
        root.resizable(True, True)
        root.configure(bg=BG)

        self._build()

    def _build(self):
        tk.Label(self.root, text="回答するアンケートを選択してください",
                 font=FONT_H2, bg=BG, fg=PRIMARY).pack(pady=(20, 12))

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=4)

        cols = ("タイトル", "種別", "設問数")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("タイトル", width=300)
        self.tree.column("種別", width=80, anchor="center")
        self.tree.column("設問数", width=70, anchor="center")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.survey_map = {}
        self._load_surveys()
        self.tree.bind("<Double-1>", lambda e: self._open_selected())

        tk.Button(self.root, text="回答を開始", font=FONT_MEDIUM, bg=PRIMARY, fg="white",
                  relief="flat", padx=16, pady=8, command=self._open_selected).pack(pady=12)

    def _load_surveys(self):
        self.tree.delete(*self.tree.get_children())
        self.survey_map.clear()
        survey_dir = get_surveys_dir()
        for fname in sorted(os.listdir(survey_dir)):
            if not fname.endswith(".json"):
                continue
            try:
                s = Survey.load(os.path.join(survey_dir, fname))
                if s.is_test_mode and s.is_anonymous:
                    mode = "匿名テスト"
                elif s.is_test_mode:
                    mode = "テスト"
                elif s.is_anonymous:
                    mode = "匿名"
                else:
                    mode = "通常"
                self.tree.insert("", "end", iid=fname,
                                 values=(s.title, mode, len(s.questions)))
                self.survey_map[fname] = s
            except Exception:
                pass

    def _open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("選択なし", "アンケートを選択してください")
            return
        fname = sel[0]
        survey = self.survey_map.get(fname)
        if not survey:
            return
        win = tk.Toplevel(self.root)
        SurveyFormWindow(win, survey)


class SurveyFormWindow:
    """アンケート回答ウィンドウ"""
    def __init__(self, root: tk.Toplevel, survey: Survey):
        self.root = root
        self.survey = survey
        root.title(f"回答 - {survey.title}")
        root.geometry("820x680")
        root.resizable(True, True)
        root.configure(bg=BG)

        self.answers: Dict[str, any] = {}
        self.department = ""
        self.name = ""
        self._users = load_master_users(get_data_path(MASTER_USER_FILE))

        self._build_header()
        self._build_name_selector()
        self._build_form()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=PRIMARY, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"📝 {self.survey.title}", font=FONT_LARGE,
                 bg=PRIMARY, fg="white").pack(side="left", padx=16, pady=10)
        if self.survey.is_anonymous:
            tk.Label(hdr, text="匿名", font=FONT_NORMAL,
                     bg="#F57F17", fg="white", padx=8, pady=3).pack(side="left", padx=4)
        if self.survey.is_test_mode:
            pts = self.survey.total_points
            tk.Label(hdr, text=f"テスト  合計 {pts} 点  合格 {self.survey.pass_score}%",
                     font=FONT_NORMAL, bg=PRIMARY, fg="#FFF9C4").pack(side="right", padx=16)

    def _build_name_selector(self):
        """部署・氏名選択エリア（匿名アンケートまたは name_selector 設問がある場合はスキップ）"""
        if self.survey.is_anonymous:
            return  # 匿名アンケートは部署・氏名を収集しない

        has_ns = any(q.type == "name_selector" for q in self.survey.questions)
        if has_ns:
            return  # フォーム内の設問として処理

        ns_frame = tk.Frame(self.root, bg="#E3F2FD", relief="flat", pady=8)
        ns_frame.pack(fill="x", padx=0)

        inner = tk.Frame(ns_frame, bg="#E3F2FD")
        inner.pack(padx=16)

        tk.Label(inner, text="部署:", font=FONT_NORMAL, bg="#E3F2FD").pack(side="left")
        depts = get_departments(self._users)
        self._dept_var = tk.StringVar()
        dept_cb = ttk.Combobox(inner, textvariable=self._dept_var, values=depts,
                               state="readonly", font=FONT_NORMAL, width=16)
        dept_cb.pack(side="left", padx=6)

        tk.Label(inner, text="氏名:", font=FONT_NORMAL, bg="#E3F2FD").pack(side="left", padx=(12, 0))
        self._name_var = tk.StringVar()
        self._name_cb = ttk.Combobox(inner, textvariable=self._name_var,
                                     state="readonly", font=FONT_NORMAL, width=16)
        self._name_cb.pack(side="left", padx=6)

        dept_cb.bind("<<ComboboxSelected>>", self._on_dept_change)
        self._top_dept_var = self._dept_var
        self._top_name_var = self._name_var

    def _on_dept_change(self, event):
        dept = self._dept_var.get()
        names = get_names_for_department(self._users, dept)
        self._name_cb["values"] = names
        self._name_var.set("")

    def _build_form(self):
        # スクロール可能フォームエリア
        canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.form_inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=self.form_inner, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        self.form_inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        from views.styles import register_scrollable
        register_scrollable(canvas)

        self._widget_map: Dict[str, dict] = {}  # qid -> {type, widget(s), frame}
        self._q_frames: Dict[str, tk.Frame] = {}

        if self.survey.description:
            desc_frame = tk.Frame(self.form_inner, bg="#E8EAF6", pady=10)
            desc_frame.pack(fill="x", padx=12, pady=(10, 4))
            tk.Label(desc_frame, text=self.survey.description, font=FONT_NORMAL,
                     bg="#E8EAF6", wraplength=700, justify="left").pack(padx=12)

        for i, q in enumerate(self.survey.questions, 1):
            self._render_question(q, i)

        # 送信ボタン
        btn_frame = tk.Frame(self.form_inner, bg=BG, pady=16)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="✔ 送信する", font=FONT_MEDIUM, bg=SUCCESS, fg="white",
                  relief="flat", padx=24, pady=10, cursor="hand2",
                  command=self._submit).pack()

        # 分岐の初期状態を適用
        self._apply_visibility()

    def _render_question(self, q: Question, num: int):
        frame = tk.Frame(self.form_inner, bg=CARD_BG, relief="ridge", bd=1)
        frame.pack(fill="x", padx=12, pady=5)
        self._q_frames[q.id] = frame

        # タイトル行
        title_row = tk.Frame(frame, bg=CARD_BG)
        title_row.pack(fill="x", padx=12, pady=(10, 4))

        # 設問番号と必須マーク
        num_label = tk.Label(title_row, text=f"Q{num}.", font=FONT_MEDIUM, bg=CARD_BG, fg=PRIMARY)
        num_label.pack(side="left")
        if q.required:
            tk.Label(title_row, text=" ＊必須", font=FONT_SMALL, bg=CARD_BG, fg=DANGER).pack(side="left")

        # 設問テキスト
        tk.Label(frame, text=q.text, font=FONT_NORMAL, bg=CARD_BG, fg=TEXT,
                 wraplength=700, justify="left", anchor="w").pack(
                     fill="x", padx=16, pady=(0, 4))

        # 参照ファイル
        if q.reference_file and os.path.exists(q.reference_file):
            tk.Button(frame, text=f"📎 参照資料を開く: {os.path.basename(q.reference_file)}",
                      font=FONT_SMALL, relief="flat", fg=PRIMARY, bg=CARD_BG, cursor="hand2",
                      command=lambda p=q.reference_file: self._open_file(p)).pack(
                          anchor="w", padx=16, pady=(0, 4))

        widget_info = {}

        if q.type == "radio":
            self._render_radio(frame, q, widget_info)
        elif q.type == "checkbox":
            self._render_checkbox(frame, q, widget_info)
        elif q.type == "dropdown":
            self._render_dropdown(frame, q, widget_info)
        elif q.type == "text":
            self._render_text(frame, q, widget_info)
        elif q.type == "textarea":
            self._render_textarea(frame, q, widget_info)
        elif q.type == "scale":
            self._render_scale(frame, q, widget_info)
        elif q.type == "name_selector":
            self._render_name_selector(frame, q, widget_info)

        widget_info["type"] = q.type
        widget_info["frame"] = frame
        self._widget_map[q.id] = widget_info

    def _render_radio(self, parent, q: Question, info: dict):
        var = tk.StringVar()
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))
        for opt in q.options:
            rb = tk.Radiobutton(opts_frame, text=opt, variable=var, value=opt,
                                font=FONT_NORMAL, bg=CARD_BG, activebackground=CARD_BG,
                                command=lambda: self._on_answer_changed(q))
            rb.pack(anchor="w", pady=2)
        info["var"] = var

    def _render_checkbox(self, parent, q: Question, info: dict):
        vars_list = []
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))
        for opt in q.options:
            v = tk.BooleanVar()
            cb = tk.Checkbutton(opts_frame, text=opt, variable=v,
                                font=FONT_NORMAL, bg=CARD_BG, activebackground=CARD_BG,
                                command=lambda: self._on_answer_changed(q))
            cb.pack(anchor="w", pady=2)
            vars_list.append((opt, v))
        info["vars"] = vars_list

    def _render_dropdown(self, parent, q: Question, info: dict):
        var = tk.StringVar()
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))
        combo = ttk.Combobox(opts_frame, textvariable=var, values=q.options,
                             state="readonly", font=FONT_NORMAL, width=28)
        combo.pack(anchor="w")
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_answer_changed(q))
        info["var"] = var

    def _render_text(self, parent, q: Question, info: dict):
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))
        var = tk.StringVar()
        entry = tk.Entry(opts_frame, textvariable=var, font=FONT_NORMAL, width=50,
                         relief="solid", bd=1)
        entry.pack(anchor="w", ipady=4)
        info["var"] = var

    def _render_textarea(self, parent, q: Question, info: dict):
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))
        text_widget = tk.Text(opts_frame, font=FONT_NORMAL, height=4, width=60,
                              relief="solid", bd=1, wrap="word")
        text_widget.pack(anchor="w")
        info["widget"] = text_widget

    def _render_scale(self, parent, q: Question, info: dict):
        var = tk.IntVar(value=0)
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))

        scale_inner = tk.Frame(opts_frame, bg=CARD_BG)
        scale_inner.pack(anchor="w")

        if q.scale_min_label:
            tk.Label(scale_inner, text=q.scale_min_label, font=FONT_SMALL, bg=CARD_BG, fg=MUTED).pack(side="left")

        for val in range(q.scale_min, q.scale_max + 1):
            col_frame = tk.Frame(scale_inner, bg=CARD_BG)
            col_frame.pack(side="left", padx=8)
            tk.Label(col_frame, text=str(val), font=FONT_NORMAL, bg=CARD_BG).pack()
            rb = tk.Radiobutton(col_frame, variable=var, value=val, bg=CARD_BG,
                                activebackground=CARD_BG,
                                command=lambda: self._on_answer_changed(q))
            rb.pack()

        if q.scale_max_label:
            tk.Label(scale_inner, text=q.scale_max_label, font=FONT_SMALL, bg=CARD_BG, fg=MUTED).pack(side="left")

        info["var"] = var

    def _render_name_selector(self, parent, q: Question, info: dict):
        opts_frame = tk.Frame(parent, bg=CARD_BG)
        opts_frame.pack(fill="x", padx=24, pady=(0, 10))

        depts = get_departments(self._users)
        dept_var = tk.StringVar()
        name_var = tk.StringVar()

        row = tk.Frame(opts_frame, bg=CARD_BG)
        row.pack(anchor="w")
        tk.Label(row, text="部署:", font=FONT_NORMAL, bg=CARD_BG).pack(side="left")
        dept_cb = ttk.Combobox(row, textvariable=dept_var, values=depts,
                               state="readonly", font=FONT_NORMAL, width=16)
        dept_cb.pack(side="left", padx=6)

        tk.Label(row, text="氏名:", font=FONT_NORMAL, bg=CARD_BG).pack(side="left", padx=(10, 0))
        name_cb = ttk.Combobox(row, textvariable=name_var, state="readonly", font=FONT_NORMAL, width=16)
        name_cb.pack(side="left", padx=6)

        def _on_dept(e):
            names = get_names_for_department(self._users, dept_var.get())
            name_cb["values"] = names
            name_var.set("")
        dept_cb.bind("<<ComboboxSelected>>", _on_dept)

        info["dept_var"] = dept_var
        info["name_var"] = name_var

    def _open_file(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開けませんでした: {e}")

    def _get_answer_value(self, q: Question) -> str:
        info = self._widget_map.get(q.id, {})
        qtype = q.type
        if qtype in ("radio", "dropdown"):
            return info.get("var", tk.StringVar()).get()
        elif qtype == "checkbox":
            selected = [opt for opt, v in info.get("vars", []) if v.get()]
            return "|||".join(selected)
        elif qtype == "text":
            return info.get("var", tk.StringVar()).get().strip()
        elif qtype == "textarea":
            w = info.get("widget")
            return w.get("1.0", "end").strip() if w else ""
        elif qtype == "scale":
            v = info.get("var", tk.IntVar()).get()
            return str(v) if v != 0 else ""
        elif qtype == "name_selector":
            dept = info.get("dept_var", tk.StringVar()).get()
            name = info.get("name_var", tk.StringVar()).get()
            if dept and name:
                self.department = dept
                self.name = name
            return f"{dept} / {name}" if dept and name else ""
        return ""

    def _on_answer_changed(self, q: Question):
        """回答が変わったとき分岐を再評価"""
        self._apply_visibility()

    def _apply_visibility(self):
        """全設問の表示/非表示を分岐ルールと表示条件に基づいて更新"""
        # まず全設問を表示
        for qid, frame in self._q_frames.items():
            frame.pack()

        # 分岐によってスキップされる設問を収集
        skipped = set()

        # 全設問を順に辿り、分岐を評価
        visible_questions = [q for q in self.survey.questions]
        skip_to = None

        for q in visible_questions:
            if skip_to:
                if q.id == skip_to:
                    skip_to = None
                else:
                    skipped.add(q.id)
                    continue

            # 表示条件チェック
            if q.show_if_question_id:
                cond_q_id = q.show_if_question_id
                cond_val = q.show_if_value
                actual = self._get_answer_value_by_id(cond_q_id)
                if actual != cond_val:
                    skipped.add(q.id)
                    continue

            # 分岐チェック
            current_answer = self._get_answer_value(q)
            for branch in q.branches:
                if current_answer == branch.condition_value:
                    skip_to = branch.jump_to_id if branch.jump_to_id else "__END__"
                    break

        # 非表示にする
        for qid in skipped:
            if qid in self._q_frames:
                self._q_frames[qid].pack_forget()

        # __END__ 以降は全部非表示
        if skip_to == "__END__":
            found = False
            for q in visible_questions:
                if found:
                    if q.id in self._q_frames:
                        self._q_frames[q.id].pack_forget()
                # skip_to == "__END__" なら全部非表示なのですでに処理済み

    def _get_answer_value_by_id(self, qid: str) -> str:
        for q in self.survey.questions:
            if q.id == qid:
                return self._get_answer_value(q)
        return ""

    def _collect_answers(self) -> Dict[str, str]:
        result = {}
        for q in self.survey.questions:
            # 非表示の設問はスキップ
            frame = self._q_frames.get(q.id)
            if frame and not frame.winfo_ismapped():
                continue
            val = self._get_answer_value(q)
            result[q.id] = val
        return result

    def _validate(self, answers: Dict[str, str]) -> List[str]:
        errors = []
        for q in self.survey.questions:
            frame = self._q_frames.get(q.id)
            if frame and not frame.winfo_ismapped():
                continue
            if q.required:
                val = answers.get(q.id, "")
                if not val:
                    errors.append(f"Q: {q.text[:40]} は必須項目です")
        return errors

    def _submit(self):
        answers = self._collect_answers()

        # 部署・氏名を取得
        if self.survey.is_anonymous:
            # 匿名アンケート: 識別情報は保存しない
            self.department = ""
            self.name = "匿名"
        else:
            has_ns = any(q.type == "name_selector" for q in self.survey.questions)
            if not has_ns:
                dept = self._top_dept_var.get() if hasattr(self, "_top_dept_var") else ""
                name = self._top_name_var.get() if hasattr(self, "_top_name_var") else ""
                if not dept or not name:
                    messagebox.showwarning("入力エラー", "部署と氏名を選択してください")
                    return
                self.department = dept
                self.name = name
            else:
                # name_selector 設問から取得済み
                if not self.department or not self.name:
                    messagebox.showwarning("入力エラー", "部署と氏名を選択してください")
                    return

        # 必須バリデーション
        errors = self._validate(answers)
        if errors:
            msg = "以下の必須項目が未入力です:\n\n" + "\n".join(f"・{e}" for e in errors)
            messagebox.showwarning("入力エラー", msg)
            return

        # 重複チェック（匿名アンケートはスキップ）
        if not self.survey.is_anonymous and not self.survey.allow_multiple_answers:
            if has_answered(get_shared_folder(), self.survey.id, self.department, self.name):
                messagebox.showwarning("回答済み", "すでに回答済みです。")
                return

        # 保存
        hostname = get_hostname()
        ip = get_ip_address()
        try:
            aid = save_answer(
                get_shared_folder(), self.survey.id,
                self.department, self.name, hostname, ip, answers)
        except Exception as e:
            messagebox.showerror("保存エラー", f"回答の保存に失敗しました:\n{e}")
            return

        try:
            write_access_log(get_data_path(ACCESS_LOG_FILE), mode="回答送信",
                             extra=f"{self.department} {self.name}")
        except Exception:
            pass

        # テストモード: 結果表示
        if self.survey.is_test_mode and self.survey.show_correct_after:
            from views.respondent.result_view import TestResultWindow
            self.root.withdraw()
            win = tk.Toplevel()
            TestResultWindow(win, self.survey, answers, self.department, self.name,
                             on_close=lambda: (self.root.destroy(), win.destroy()))
        else:
            messagebox.showinfo("送信完了", "回答を送信しました。ご協力ありがとうございます！")
            self.root.destroy()
