"""
アンケート編集ウィンドウ
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import uuid
import os

from models.survey import Survey, Question, BranchRule, QUESTION_TYPES
from views.styles import (PRIMARY, DANGER, SUCCESS, WARNING, BG, CARD_BG, FONT_LARGE, FONT_NORMAL,
                           FONT_MEDIUM, FONT_H2, MUTED, BORDER, TEXT, FONT_SMALL)


class SurveyEditorWindow:
    def __init__(self, root: tk.Toplevel, survey: Survey, fpath: str, on_close_callback=None):
        self.root = root
        self.survey = survey
        self.fpath = fpath
        self.on_close_callback = on_close_callback

        self.root.title(f"アンケート編集 - {survey.title}")
        self.root.geometry("980x720")
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build()
        self._refresh_question_list()

    def _build(self):
        # --- ヘッダー ---
        hdr = tk.Frame(self.root, bg=PRIMARY, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📋 アンケート編集", font=FONT_LARGE, bg=PRIMARY, fg="white").pack(
            side="left", padx=16, pady=10)
        tk.Button(hdr, text="💾 保存して閉じる", font=FONT_NORMAL, bg=SUCCESS, fg="white",
                  relief="flat", padx=12, pady=4, command=self._save_and_close).pack(side="right", padx=12, pady=8)
        tk.Button(hdr, text="💾 保存", font=FONT_NORMAL, bg="#1976D2", fg="white",
                  relief="flat", padx=12, pady=4, command=self._save).pack(side="right", padx=4, pady=8)

        # --- 左右分割 ---
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # === 左ペイン: アンケート基本設定 + 設問リスト ===
        left = ttk.Frame(paned, width=340)
        paned.add(left, weight=1)

        # 基本設定
        cfg_frame = tk.LabelFrame(left, text="  基本設定  ", font=FONT_NORMAL, bg=BG,
                                   fg=PRIMARY, padx=10, pady=8)
        cfg_frame.pack(fill="x", padx=8, pady=8)

        tk.Label(cfg_frame, text="タイトル:", font=FONT_NORMAL, bg=BG).grid(row=0, column=0, sticky="w", pady=3)
        self.title_var = tk.StringVar(value=self.survey.title)
        tk.Entry(cfg_frame, textvariable=self.title_var, font=FONT_NORMAL, width=28,
                 relief="solid", bd=1).grid(row=0, column=1, sticky="ew", pady=3, padx=(6, 0))

        tk.Label(cfg_frame, text="説明文:", font=FONT_NORMAL, bg=BG).grid(row=1, column=0, sticky="nw", pady=3)
        self.desc_text = tk.Text(cfg_frame, font=FONT_NORMAL, width=28, height=3, relief="solid", bd=1)
        self.desc_text.insert("1.0", self.survey.description)
        self.desc_text.grid(row=1, column=1, sticky="ew", pady=3, padx=(6, 0))

        # テストモード
        self.is_test_var = tk.BooleanVar(value=self.survey.is_test_mode)
        tk.Checkbutton(cfg_frame, text="テストモードを有効にする", variable=self.is_test_var,
                       font=FONT_NORMAL, bg=BG, command=self._toggle_test_mode).grid(
                           row=2, column=0, columnspan=2, sticky="w", pady=3)

        self.test_frame = tk.Frame(cfg_frame, bg=BG)
        self.test_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        tk.Label(self.test_frame, text="合格ライン(%):", font=FONT_NORMAL, bg=BG).pack(side="left")
        self.pass_score_var = tk.IntVar(value=self.survey.pass_score)
        tk.Spinbox(self.test_frame, from_=0, to=100, textvariable=self.pass_score_var,
                   font=FONT_NORMAL, width=5).pack(side="left", padx=4)
        self.show_correct_var = tk.BooleanVar(value=self.survey.show_correct_after)
        tk.Checkbutton(self.test_frame, text="終了後に正解を表示", variable=self.show_correct_var,
                       font=FONT_NORMAL, bg=BG).pack(side="left", padx=8)

        # 匿名アンケート（完全匿名）
        self.is_anon_var = tk.BooleanVar(value=self.survey.is_anonymous)
        tk.Checkbutton(cfg_frame, text="完全匿名（部署・氏名を収集しない）",
                       variable=self.is_anon_var, font=FONT_NORMAL, bg=BG,
                       command=self._toggle_anon_mode).grid(
                           row=4, column=0, columnspan=2, sticky="w", pady=3)

        # 部署のみ匿名
        self.anon_name_only_var = tk.BooleanVar(value=self.survey.anonymous_name_only)
        tk.Checkbutton(cfg_frame, text="部署のみ匿名（部署は保存、氏名は「匿名」として保存）",
                       variable=self.anon_name_only_var, font=FONT_NORMAL, bg=BG).grid(
                           row=5, column=0, columnspan=2, sticky="w", pady=2)

        self.anon_note = tk.Label(cfg_frame,
                                  text="  ※ 完全匿名時は回答者識別・重複チェックを行いません。",
                                  font=("Yu Gothic UI", 9), bg=BG, fg="#F57F17")
        self.anon_note.grid(row=6, column=0, columnspan=2, sticky="w")

        self.multi_answer_var = tk.BooleanVar(value=self.survey.allow_multiple_answers)
        self.multi_answer_cb = tk.Checkbutton(cfg_frame, text="同一ユーザーの複数回答を許可",
                                              variable=self.multi_answer_var,
                                              font=FONT_NORMAL, bg=BG)
        self.multi_answer_cb.grid(row=7, column=0, columnspan=2, sticky="w", pady=3)

        # 期限設定
        tk.Label(cfg_frame, text="開始日:", font=FONT_NORMAL, bg=BG).grid(
            row=8, column=0, sticky="w", pady=3)
        date_row = tk.Frame(cfg_frame, bg=BG)
        date_row.grid(row=8, column=1, sticky="ew", pady=3, padx=(6, 0))
        self.start_date_var = tk.StringVar(value=self.survey.start_date)
        tk.Entry(date_row, textvariable=self.start_date_var, font=FONT_NORMAL, width=12,
                 relief="solid", bd=1).pack(side="left")
        tk.Label(date_row, text=" YYYY-MM-DD（空=制限なし）", font=("Yu Gothic UI", 9),
                 bg=BG, fg=MUTED).pack(side="left", padx=4)

        tk.Label(cfg_frame, text="終了日:", font=FONT_NORMAL, bg=BG).grid(
            row=9, column=0, sticky="w", pady=3)
        date_row2 = tk.Frame(cfg_frame, bg=BG)
        date_row2.grid(row=9, column=1, sticky="ew", pady=3, padx=(6, 0))
        self.end_date_var = tk.StringVar(value=self.survey.end_date)
        tk.Entry(date_row2, textvariable=self.end_date_var, font=FONT_NORMAL, width=12,
                 relief="solid", bd=1).pack(side="left")
        tk.Label(date_row2, text=" YYYY-MM-DD（空=制限なし）", font=("Yu Gothic UI", 9),
                 bg=BG, fg=MUTED).pack(side="left", padx=4)

        # アンケートパスワード
        tk.Label(cfg_frame, text="編集/集計PW:", font=FONT_NORMAL, bg=BG).grid(
            row=10, column=0, sticky="w", pady=3)
        pw_row = tk.Frame(cfg_frame, bg=BG)
        pw_row.grid(row=10, column=1, sticky="ew", pady=3, padx=(6, 0))
        self.survey_pw_var = tk.StringVar(value=self.survey.survey_password)
        tk.Entry(pw_row, textvariable=self.survey_pw_var, font=FONT_NORMAL, width=16,
                 relief="solid", bd=1, show="*").pack(side="left")
        tk.Label(pw_row, text=" 空=パスワードなし", font=("Yu Gothic UI", 9),
                 bg=BG, fg=MUTED).pack(side="left", padx=4)

        cfg_frame.columnconfigure(1, weight=1)
        self._toggle_test_mode()
        self._toggle_anon_mode()

        # ── 終了画面設定 ──
        comp_frame = tk.LabelFrame(left, text="  終了画面設定  ", font=FONT_NORMAL,
                                   bg=BG, fg="#00695C", padx=8, pady=6)
        comp_frame.pack(fill="x", padx=8, pady=(0, 4))

        tk.Label(comp_frame, text="メッセージ:", font=FONT_NORMAL, bg=BG).grid(
            row=0, column=0, sticky="nw", pady=3)
        self._comp_text = tk.Text(comp_frame, font=FONT_NORMAL, width=26, height=3,
                                  relief="solid", bd=1)
        self._comp_text.insert("1.0", self.survey.completion_text)
        self._comp_text.grid(row=0, column=1, sticky="ew", pady=3, padx=(4, 0))

        tk.Label(comp_frame, text="画像ファイル:", font=FONT_NORMAL, bg=BG).grid(
            row=1, column=0, sticky="w", pady=3)
        img_row = tk.Frame(comp_frame, bg=BG)
        img_row.grid(row=1, column=1, sticky="ew", pady=3, padx=(4, 0))
        self._comp_img_var = tk.StringVar(value=self.survey.completion_image_path)
        tk.Entry(img_row, textvariable=self._comp_img_var, font=FONT_NORMAL, width=18,
                 relief="solid", bd=1).pack(side="left", fill="x", expand=True)
        tk.Button(img_row, text="参照…", font=FONT_SMALL, relief="flat",
                  command=lambda: self._browse_image(self._comp_img_var)).pack(side="left", padx=2)

        tk.Label(comp_frame, text="PDF / テキスト:", font=FONT_NORMAL, bg=BG).grid(
            row=2, column=0, sticky="w", pady=3)
        pdf_row = tk.Frame(comp_frame, bg=BG)
        pdf_row.grid(row=2, column=1, sticky="ew", pady=3, padx=(4, 0))
        self._comp_pdf_var = tk.StringVar(value=self.survey.completion_pdf_path)
        tk.Entry(pdf_row, textvariable=self._comp_pdf_var, font=FONT_NORMAL, width=18,
                 relief="solid", bd=1).pack(side="left", fill="x", expand=True)
        tk.Button(pdf_row, text="参照…", font=FONT_SMALL, relief="flat",
                  command=lambda: self._browse_pdf(self._comp_pdf_var)).pack(side="left", padx=2)

        comp_frame.columnconfigure(1, weight=1)

        # 設問リスト
        q_frame = tk.LabelFrame(left, text="  設問一覧  ", font=FONT_NORMAL, bg=BG, fg=PRIMARY)
        q_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        q_btn_frame = tk.Frame(q_frame, bg=BG)
        q_btn_frame.pack(fill="x", pady=4)
        tk.Button(q_btn_frame, text="＋ 追加", font=FONT_NORMAL, bg=SUCCESS, fg="white",
                  relief="flat", padx=8, pady=3, command=self._add_question).pack(side="left", padx=2)
        tk.Button(q_btn_frame, text="↑", font=FONT_NORMAL, relief="flat", padx=8, pady=3,
                  command=self._move_up).pack(side="left", padx=2)
        tk.Button(q_btn_frame, text="↓", font=FONT_NORMAL, relief="flat", padx=8, pady=3,
                  command=self._move_down).pack(side="left", padx=2)
        tk.Button(q_btn_frame, text="🗑️ 削除", font=FONT_NORMAL, bg=DANGER, fg="white",
                  relief="flat", padx=8, pady=3, command=self._delete_question).pack(side="left", padx=2)

        self.q_listbox = tk.Listbox(q_frame, font=FONT_NORMAL, selectmode="single",
                                    relief="solid", bd=1, height=16, activestyle="none",
                                    selectbackground=PRIMARY, selectforeground="white")
        q_scroll = ttk.Scrollbar(q_frame, orient="vertical", command=self.q_listbox.yview)
        self.q_listbox.configure(yscrollcommand=q_scroll.set)
        self.q_listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        q_scroll.pack(side="right", fill="y", pady=4, padx=(0, 4))
        self.q_listbox.bind("<<ListboxSelect>>", self._on_question_select)

        # === 右ペイン: 設問詳細エディタ ===
        self.right = ttk.Frame(paned)
        paned.add(self.right, weight=2)
        self._detail_placeholder()

    def _toggle_test_mode(self):
        if self.is_test_var.get():
            self.test_frame.grid()
        else:
            self.test_frame.grid_remove()

    def _toggle_anon_mode(self):
        if self.is_anon_var.get():
            self.anon_note.grid()
            self.multi_answer_cb.grid_remove()   # 匿名時は重複チェック設定を隠す
        else:
            self.anon_note.grid_remove()
            self.multi_answer_cb.grid()

    # ──────────────────────────────────────
    # 設問リスト操作
    # ──────────────────────────────────────
    def _refresh_question_list(self):
        self.q_listbox.delete(0, "end")
        for i, q in enumerate(self.survey.questions, 1):
            label = f"Q{i}. [{QUESTION_TYPES.get(q.type, q.type)}] {q.text[:30]}{'…' if len(q.text) > 30 else ''}"
            if q.required:
                label += " *"
            self.q_listbox.insert("end", label)

    def _add_question(self):
        qid = str(uuid.uuid4())[:8]
        q = Question(id=qid, type="radio", text="新しい設問", required=False)
        self.survey.questions.append(q)
        self._refresh_question_list()
        self.q_listbox.selection_clear(0, "end")
        idx = len(self.survey.questions) - 1
        self.q_listbox.selection_set(idx)
        self._show_question_editor(idx)

    def _delete_question(self):
        sel = self.q_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if messagebox.askyesno("確認", "この設問を削除しますか？"):
            del self.survey.questions[idx]
            self._refresh_question_list()
            self._detail_placeholder()

    def _move_up(self):
        sel = self.q_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self.survey.questions[i - 1], self.survey.questions[i] = \
            self.survey.questions[i], self.survey.questions[i - 1]
        self._refresh_question_list()
        self.q_listbox.selection_set(i - 1)

    def _move_down(self):
        sel = self.q_listbox.curselection()
        if not sel or sel[0] == len(self.survey.questions) - 1:
            return
        i = sel[0]
        self.survey.questions[i], self.survey.questions[i + 1] = \
            self.survey.questions[i + 1], self.survey.questions[i]
        self._refresh_question_list()
        self.q_listbox.selection_set(i + 1)

    def _on_question_select(self, event):
        sel = self.q_listbox.curselection()
        if sel:
            self._show_question_editor(sel[0])

    # ──────────────────────────────────────
    # 右ペイン: 設問詳細エディタ
    # ──────────────────────────────────────
    def _clear_right(self):
        for w in self.right.winfo_children():
            w.destroy()

    def _detail_placeholder(self):
        self._clear_right()
        tk.Label(self.right, text="設問を選択してください", font=FONT_LARGE,
                 bg=BG, fg=MUTED).pack(expand=True)

    def _show_question_editor(self, idx: int):
        self._clear_right()
        q = self.survey.questions[idx]

        # スクロール可能エリア
        canvas = tk.Canvas(self.right, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self.right, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        from views.styles import register_scrollable
        register_scrollable(canvas)

        pad = dict(padx=16, pady=5)

        # 設問番号タイトル
        q_num = idx + 1
        tk.Label(inner, text=f"Q{q_num} 設問エディタ", font=FONT_H2, bg=BG, fg=PRIMARY).pack(
            fill="x", **pad)
        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=16, pady=4)

        # 設問タイプ
        type_frame = tk.Frame(inner, bg=BG)
        type_frame.pack(fill="x", **pad)
        tk.Label(type_frame, text="設問タイプ:", font=FONT_NORMAL, bg=BG, width=14, anchor="w").pack(side="left")
        self._q_type_var = tk.StringVar(value=q.type)
        type_combo = ttk.Combobox(type_frame, textvariable=self._q_type_var,
                                  values=list(QUESTION_TYPES.keys()),
                                  state="readonly", font=FONT_NORMAL, width=18)
        type_combo.pack(side="left", padx=4)
        tk.Label(type_frame, text=QUESTION_TYPES.get(q.type, ""), font=FONT_SMALL, bg=BG, fg=MUTED).pack(side="left", padx=4)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._on_type_changed(q, idx, type_combo))

        # 設問文
        text_frame = tk.Frame(inner, bg=BG)
        text_frame.pack(fill="x", **pad)
        tk.Label(text_frame, text="設問文:", font=FONT_NORMAL, bg=BG, width=14, anchor="w").pack(side="left", anchor="n")
        self._q_text = tk.Text(text_frame, font=FONT_NORMAL, height=3, width=40, relief="solid", bd=1)
        self._q_text.insert("1.0", q.text)
        self._q_text.pack(side="left", fill="x", expand=True, padx=4)

        # 必須・参照ファイル
        meta_frame = tk.Frame(inner, bg=BG)
        meta_frame.pack(fill="x", **pad)
        self._q_required_var = tk.BooleanVar(value=q.required)
        tk.Checkbutton(meta_frame, text="必須項目", variable=self._q_required_var,
                       font=FONT_NORMAL, bg=BG).pack(side="left", padx=(80, 20))

        tk.Label(meta_frame, text="参照ファイル(PDF等):", font=FONT_NORMAL, bg=BG).pack(side="left")
        self._q_ref_var = tk.StringVar(value=q.reference_file)
        tk.Entry(meta_frame, textvariable=self._q_ref_var, font=FONT_NORMAL, width=22,
                 relief="solid", bd=1).pack(side="left", padx=4)
        tk.Button(meta_frame, text="参照…", font=FONT_SMALL, relief="flat",
                  command=lambda: self._browse_file(self._q_ref_var)).pack(side="left")

        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=16, pady=6)

        # タイプ別設定エリア
        self._type_options_frame = tk.Frame(inner, bg=BG)
        self._type_options_frame.pack(fill="x", **pad)
        self._build_type_options(self._type_options_frame, q, idx)

        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=16, pady=6)

        # 分岐設定
        self._build_branch_editor(inner, q, idx)

        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=16, pady=6)

        # 表示条件
        self._build_show_if_editor(inner, q, idx)

        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=16, pady=6)

        # 適用ボタン
        tk.Button(inner, text="✔ この設問に変更を適用", font=FONT_MEDIUM,
                  bg=PRIMARY, fg="white", relief="flat", padx=16, pady=8,
                  command=lambda: self._apply_question(q, idx)).pack(pady=10)

    def _on_type_changed(self, q: Question, idx: int, combo: ttk.Combobox):
        q.type = self._q_type_var.get()
        for w in self._type_options_frame.winfo_children():
            w.destroy()
        self._build_type_options(self._type_options_frame, q, idx)

    def _build_type_options(self, parent: tk.Frame, q: Question, idx: int):
        qtype = self._q_type_var.get()

        if qtype in ("radio", "checkbox", "dropdown"):
            tk.Label(parent, text="選択肢:", font=FONT_NORMAL, bg=BG).pack(anchor="w")
            opt_frame = tk.Frame(parent, bg=BG)
            opt_frame.pack(fill="x")
            self._opt_listbox = tk.Listbox(opt_frame, font=FONT_NORMAL, height=8,
                                           relief="solid", bd=1, selectmode="single",
                                           selectbackground=PRIMARY, selectforeground="white")
            self._opt_listbox.pack(side="left", fill="both", expand=True)
            for opt in q.options:
                self._opt_listbox.insert("end", opt)

            opt_btn = tk.Frame(opt_frame, bg=BG)
            opt_btn.pack(side="right", padx=4)
            tk.Button(opt_btn, text="追加", font=FONT_NORMAL, relief="flat",
                      command=self._add_option).pack(pady=2, fill="x")
            tk.Button(opt_btn, text="編集", font=FONT_NORMAL, relief="flat",
                      command=self._edit_option).pack(pady=2, fill="x")
            tk.Button(opt_btn, text="削除", font=FONT_NORMAL, bg=DANGER, fg="white",
                      relief="flat", command=self._delete_option).pack(pady=2, fill="x")
            tk.Button(opt_btn, text="↑", font=FONT_NORMAL, relief="flat",
                      command=self._move_opt_up).pack(pady=2, fill="x")
            tk.Button(opt_btn, text="↓", font=FONT_NORMAL, relief="flat",
                      command=self._move_opt_down).pack(pady=2, fill="x")

            # テストモード: 正解設定
            if self.is_test_var.get():
                tk.Label(parent, text="正解（テスト用）:", font=FONT_NORMAL, bg=BG).pack(anchor="w", pady=(8, 2))
                self._correct_listbox = tk.Listbox(parent, font=FONT_NORMAL, height=4,
                                                   relief="solid", bd=1, selectmode="multiple",
                                                   selectbackground=SUCCESS, selectforeground="white")
                self._correct_listbox.pack(fill="x")
                for opt in q.options:
                    self._correct_listbox.insert("end", opt)
                for i, opt in enumerate(q.options):
                    if opt in q.correct_answers:
                        self._correct_listbox.selection_set(i)
                tk.Label(parent, text="※ 正解の選択肢を選んでください（複数可）",
                         font=FONT_SMALL, bg=BG, fg=MUTED).pack(anchor="w")

                pts_frame = tk.Frame(parent, bg=BG)
                pts_frame.pack(anchor="w", pady=4)
                tk.Label(pts_frame, text="配点:", font=FONT_NORMAL, bg=BG).pack(side="left")
                self._q_points_var = tk.IntVar(value=q.points)
                tk.Spinbox(pts_frame, from_=0, to=100, textvariable=self._q_points_var,
                           font=FONT_NORMAL, width=5).pack(side="left", padx=4)
                tk.Label(pts_frame, text="点", font=FONT_NORMAL, bg=BG).pack(side="left")
            else:
                self._correct_listbox = None
                self._q_points_var = tk.IntVar(value=q.points)

        elif qtype == "scale":
            sf = tk.Frame(parent, bg=BG)
            sf.pack(fill="x")
            tk.Label(sf, text="最小値:", font=FONT_NORMAL, bg=BG).grid(row=0, column=0, sticky="w", pady=3)
            self._scale_min_var = tk.IntVar(value=q.scale_min)
            tk.Spinbox(sf, from_=0, to=10, textvariable=self._scale_min_var,
                       font=FONT_NORMAL, width=5).grid(row=0, column=1, pady=3, padx=4)
            tk.Label(sf, text="最小ラベル:", font=FONT_NORMAL, bg=BG).grid(row=0, column=2, sticky="w", padx=8)
            self._scale_min_label_var = tk.StringVar(value=q.scale_min_label)
            tk.Entry(sf, textvariable=self._scale_min_label_var, font=FONT_NORMAL, width=12,
                     relief="solid", bd=1).grid(row=0, column=3, pady=3)

            tk.Label(sf, text="最大値:", font=FONT_NORMAL, bg=BG).grid(row=1, column=0, sticky="w", pady=3)
            self._scale_max_var = tk.IntVar(value=q.scale_max)
            tk.Spinbox(sf, from_=1, to=10, textvariable=self._scale_max_var,
                       font=FONT_NORMAL, width=5).grid(row=1, column=1, pady=3, padx=4)
            tk.Label(sf, text="最大ラベル:", font=FONT_NORMAL, bg=BG).grid(row=1, column=2, sticky="w", padx=8)
            self._scale_max_label_var = tk.StringVar(value=q.scale_max_label)
            tk.Entry(sf, textvariable=self._scale_max_label_var, font=FONT_NORMAL, width=12,
                     relief="solid", bd=1).grid(row=1, column=3, pady=3)

            if self.is_test_var.get():
                pf = tk.Frame(parent, bg=BG)
                pf.pack(anchor="w", pady=4)
                tk.Label(pf, text="配点:", font=FONT_NORMAL, bg=BG).pack(side="left")
                self._q_points_var = tk.IntVar(value=q.points)
                tk.Spinbox(pf, from_=0, to=100, textvariable=self._q_points_var,
                           font=FONT_NORMAL, width=5).pack(side="left", padx=4)
            else:
                self._q_points_var = tk.IntVar(value=q.points)
                self._scale_min_var = getattr(self, "_scale_min_var", tk.IntVar(value=1))
                self._scale_max_var = getattr(self, "_scale_max_var", tk.IntVar(value=5))
                self._scale_min_label_var = getattr(self, "_scale_min_label_var", tk.StringVar())
                self._scale_max_label_var = getattr(self, "_scale_max_label_var", tk.StringVar())

        elif qtype == "name_selector":
            tk.Label(parent, text="部署・氏名は master_user.csv から自動的に読み込まれます。",
                     font=FONT_NORMAL, bg=BG, fg=MUTED, wraplength=400, justify="left").pack(anchor="w")

        else:  # text, textarea
            tk.Label(parent, text="テキスト入力フィールドです（選択肢なし）。",
                     font=FONT_NORMAL, bg=BG, fg=MUTED).pack(anchor="w")
            if self.is_test_var.get():
                ca_frame = tk.Frame(parent, bg=BG)
                ca_frame.pack(anchor="w", pady=4)
                tk.Label(ca_frame, text="正解キーワード:", font=FONT_NORMAL, bg=BG).pack(side="left")
                self._correct_text_var = tk.StringVar(
                    value=q.correct_answers[0] if q.correct_answers else "")
                tk.Entry(ca_frame, textvariable=self._correct_text_var, font=FONT_NORMAL, width=20,
                         relief="solid", bd=1).pack(side="left", padx=4)
                pf = tk.Frame(parent, bg=BG)
                pf.pack(anchor="w", pady=4)
                tk.Label(pf, text="配点:", font=FONT_NORMAL, bg=BG).pack(side="left")
                self._q_points_var = tk.IntVar(value=q.points)
                tk.Spinbox(pf, from_=0, to=100, textvariable=self._q_points_var,
                           font=FONT_NORMAL, width=5).pack(side="left", padx=4)
            else:
                self._q_points_var = tk.IntVar(value=q.points)

    def _build_branch_editor(self, parent: tk.Frame, q: Question, idx: int):
        lf = tk.LabelFrame(parent, text="  分岐設定  ", font=FONT_NORMAL, bg=BG, fg=PRIMARY, padx=8, pady=6)
        lf.pack(fill="x", padx=16)
        tk.Label(lf, text="指定の回答があった場合、特定の設問にジャンプします。",
                 font=FONT_SMALL, bg=BG, fg=MUTED).pack(anchor="w")

        # 分岐リスト
        self._branch_listbox = tk.Listbox(lf, font=FONT_NORMAL, height=4,
                                          relief="solid", bd=1, selectmode="single",
                                          selectbackground=WARNING, selectforeground="white")
        self._branch_listbox.pack(fill="x", pady=4)
        self._refresh_branch_list(q)

        btn_row = tk.Frame(lf, bg=BG)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="＋ 分岐を追加", font=FONT_NORMAL, relief="flat",
                  command=lambda: self._add_branch(q, idx)).pack(side="left", padx=2)
        tk.Button(btn_row, text="🗑️ 削除", font=FONT_NORMAL, bg=DANGER, fg="white",
                  relief="flat", command=lambda: self._delete_branch(q)).pack(side="left", padx=2)

    def _refresh_branch_list(self, q: Question):
        self._branch_listbox.delete(0, "end")
        for b in q.branches:
            dest = b.jump_to_id if b.jump_to_id else "（アンケート終了）"
            self._branch_listbox.insert("end", f"回答「{b.condition_value}」→ 設問 {dest}")

    def _add_branch(self, q: Question, idx: int):
        dlg = BranchDialog(self._type_options_frame.winfo_toplevel(), q, self.survey.questions)
        if dlg.result:
            q.branches.append(dlg.result)
            self._refresh_branch_list(q)

    def _delete_branch(self, q: Question):
        sel = self._branch_listbox.curselection()
        if sel:
            del q.branches[sel[0]]
            self._refresh_branch_list(q)

    def _build_show_if_editor(self, parent: tk.Frame, q: Question, idx: int):
        lf = tk.LabelFrame(parent, text="  表示条件  ", font=FONT_NORMAL, bg=BG, fg="#6A1B9A",
                            padx=8, pady=6)
        lf.pack(fill="x", padx=16)
        tk.Label(lf, text="指定の設問が特定の値に回答された場合のみ、この設問を表示します。",
                 font=FONT_SMALL, bg=BG, fg=MUTED, wraplength=500).pack(anchor="w")

        row = tk.Frame(lf, bg=BG)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="設問ID:", font=FONT_NORMAL, bg=BG).pack(side="left")
        self._show_if_qid_var = tk.StringVar(value=q.show_if_question_id)
        qid_combo = ttk.Combobox(row, textvariable=self._show_if_qid_var, font=FONT_NORMAL, width=12,
                                 values=[""] + [qq.id for jj, qq in enumerate(self.survey.questions) if jj != idx])
        qid_combo.pack(side="left", padx=4)
        tk.Label(row, text="の回答が：", font=FONT_NORMAL, bg=BG).pack(side="left")
        self._show_if_val_var = tk.StringVar(value=q.show_if_value)
        tk.Entry(row, textvariable=self._show_if_val_var, font=FONT_NORMAL, width=14,
                 relief="solid", bd=1).pack(side="left", padx=4)
        tk.Label(row, text="の場合に表示", font=FONT_NORMAL, bg=BG).pack(side="left")

    # ──────────────────────────────────────
    # オプション操作
    # ──────────────────────────────────────
    def _get_options(self):
        return list(self._opt_listbox.get(0, "end"))

    def _add_option(self):
        val = simpledialog.askstring("選択肢追加", "選択肢のテキストを入力:")
        if val:
            self._opt_listbox.insert("end", val)
            if hasattr(self, "_correct_listbox") and self._correct_listbox:
                self._correct_listbox.insert("end", val)

    def _edit_option(self):
        sel = self._opt_listbox.curselection()
        if not sel:
            return
        old = self._opt_listbox.get(sel[0])
        val = simpledialog.askstring("選択肢編集", "選択肢のテキストを入力:", initialvalue=old)
        if val:
            self._opt_listbox.delete(sel[0])
            self._opt_listbox.insert(sel[0], val)
            if hasattr(self, "_correct_listbox") and self._correct_listbox:
                self._correct_listbox.delete(sel[0])
                self._correct_listbox.insert(sel[0], val)

    def _delete_option(self):
        sel = self._opt_listbox.curselection()
        if sel:
            self._opt_listbox.delete(sel[0])
            if hasattr(self, "_correct_listbox") and self._correct_listbox:
                self._correct_listbox.delete(sel[0])

    def _move_opt_up(self):
        sel = self._opt_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        for lb in [self._opt_listbox] + ([self._correct_listbox] if getattr(self, "_correct_listbox", None) else []):
            v0, v1 = lb.get(i - 1), lb.get(i)
            lb.delete(i - 1, i)
            lb.insert(i - 1, v1)
            lb.insert(i, v0)
        self._opt_listbox.selection_set(i - 1)

    def _move_opt_down(self):
        sel = self._opt_listbox.curselection()
        n = self._opt_listbox.size()
        if not sel or sel[0] == n - 1:
            return
        i = sel[0]
        for lb in [self._opt_listbox] + ([self._correct_listbox] if getattr(self, "_correct_listbox", None) else []):
            v0, v1 = lb.get(i), lb.get(i + 1)
            lb.delete(i, i + 1)
            lb.insert(i, v1)
            lb.insert(i + 1, v0)
        self._opt_listbox.selection_set(i + 1)

    def _browse_file(self, var: tk.StringVar):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("全ファイル", "*.*"), ("PDF", "*.pdf")])
        if path:
            var.set(path)

    def _browse_image(self, var: tk.StringVar):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="画像ファイルを選択",
            filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                       ("全ファイル", "*.*")])
        if path:
            var.set(path)

    def _browse_pdf(self, var: tk.StringVar):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="PDF / テキストファイルを選択",
            filetypes=[("PDF", "*.pdf"), ("テキスト", "*.txt"),
                       ("全ファイル", "*.*")])
        if path:
            var.set(path)

    # ──────────────────────────────────────
    # 変更の適用
    # ──────────────────────────────────────
    def _apply_question(self, q: Question, idx: int):
        q.type = self._q_type_var.get()
        q.text = self._q_text.get("1.0", "end").strip()
        q.required = self._q_required_var.get()
        q.reference_file = self._q_ref_var.get().strip()
        q.points = getattr(self, "_q_points_var", tk.IntVar(value=1)).get()
        q.show_if_question_id = self._show_if_qid_var.get().strip()
        q.show_if_value = self._show_if_val_var.get().strip()

        if q.type in ("radio", "checkbox", "dropdown"):
            q.options = self._get_options()
            if hasattr(self, "_correct_listbox") and self._correct_listbox:
                sel = self._correct_listbox.curselection()
                q.correct_answers = [self._correct_listbox.get(i) for i in sel]
            else:
                q.correct_answers = []
        elif q.type == "scale":
            q.scale_min = getattr(self, "_scale_min_var", tk.IntVar(value=1)).get()
            q.scale_max = getattr(self, "_scale_max_var", tk.IntVar(value=5)).get()
            q.scale_min_label = getattr(self, "_scale_min_label_var", tk.StringVar()).get()
            q.scale_max_label = getattr(self, "_scale_max_label_var", tk.StringVar()).get()
        elif q.type in ("text", "textarea"):
            if hasattr(self, "_correct_text_var"):
                v = self._correct_text_var.get().strip()
                q.correct_answers = [v] if v else []

        self._refresh_question_list()
        messagebox.showinfo("適用完了", f"Q{idx + 1} の変更を適用しました。\n保存ボタンで確定してください。")

    # ──────────────────────────────────────
    # 保存
    # ──────────────────────────────────────
    def _save(self):
        self.survey.title = self.title_var.get().strip() or "無題のアンケート"
        self.survey.description = self.desc_text.get("1.0", "end").strip()
        self.survey.is_test_mode = self.is_test_var.get()
        self.survey.is_anonymous = self.is_anon_var.get()
        self.survey.anonymous_name_only = self.anon_name_only_var.get()
        self.survey.start_date = self.start_date_var.get().strip()
        self.survey.end_date = self.end_date_var.get().strip()
        self.survey.survey_password = self.survey_pw_var.get()
        self.survey.completion_text = self._comp_text.get("1.0", "end").strip()
        self.survey.completion_image_path = self._comp_img_var.get().strip()
        self.survey.completion_pdf_path = self._comp_pdf_var.get().strip()
        self.survey.pass_score = self.pass_score_var.get()
        self.survey.show_correct_after = self.show_correct_var.get()
        self.survey.allow_multiple_answers = self.multi_answer_var.get()
        self.survey.save(self.fpath)
        messagebox.showinfo("保存", "アンケートを保存しました。")

    def _save_and_close(self):
        self._save()
        self._on_close()

    def _on_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.root.destroy()


class BranchDialog:
    """分岐ルールを追加するダイアログ"""
    def __init__(self, parent, q: Question, all_questions: list):
        self.result = None
        dlg = tk.Toplevel(parent)
        dlg.title("分岐ルールの追加")
        dlg.geometry("400x260")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(bg=CARD_BG)

        tk.Label(dlg, text="条件となる回答値:", font=FONT_NORMAL, bg=CARD_BG).pack(pady=(20, 4))
        cond_var = tk.StringVar()
        if q.type in ("radio", "checkbox", "dropdown") and q.options:
            combo = ttk.Combobox(dlg, textvariable=cond_var, values=q.options,
                                 font=FONT_NORMAL, width=24)
            combo.pack()
        else:
            tk.Entry(dlg, textvariable=cond_var, font=FONT_NORMAL, width=24,
                     relief="solid", bd=1).pack()

        tk.Label(dlg, text="ジャンプ先の設問ID（空=終了）:", font=FONT_NORMAL, bg=CARD_BG).pack(pady=(14, 4))
        jump_var = tk.StringVar()
        q_ids = ["（アンケートを終了）"] + [f"{qq.id} - {qq.text[:20]}" for qq in all_questions]
        jump_combo = ttk.Combobox(dlg, textvariable=jump_var, values=q_ids,
                                  font=FONT_NORMAL, width=30)
        jump_combo.pack()

        def _ok():
            cond = cond_var.get().strip()
            jv = jump_var.get().strip()
            jid = "" if "終了" in jv else jv.split(" - ")[0]
            if cond:
                self.result = BranchRule(condition_value=cond, jump_to_id=jid)
            dlg.destroy()

        tk.Button(dlg, text="追加", font=FONT_NORMAL, bg=PRIMARY, fg="white",
                  relief="flat", padx=14, pady=6, command=_ok).pack(pady=16)
        dlg.wait_window()
