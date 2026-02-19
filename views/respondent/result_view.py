"""
テスト結果表示ウィンドウ
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional

from models.survey import Survey, Question, QUESTION_TYPES
from views.styles import (PRIMARY, BG, CARD_BG, FONT_LARGE, FONT_NORMAL, FONT_MEDIUM,
                           FONT_H2, FONT_SMALL, MUTED, DANGER, SUCCESS, WARNING, CORRECT, INCORRECT, TEXT)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def _is_correct(q: Question, answer: str) -> bool:
    """回答が正解かどうかを判定"""
    if not q.correct_answers:
        return True  # 正解未設定 = 常に正解

    if q.type == "checkbox":
        given = set(a.strip() for a in answer.split("|||") if a.strip())
        correct = set(q.correct_answers)
        return given == correct
    elif q.type in ("text", "textarea"):
        # キーワード部分一致
        return any(kw.lower() in answer.lower() for kw in q.correct_answers if kw)
    else:
        return answer in q.correct_answers


class TestResultWindow:
    def __init__(self, root: tk.Toplevel, survey: Survey,
                 answers: Dict[str, str],
                 department: str, name: str,
                 on_close: Optional[Callable] = None):
        self.root = root
        self.survey = survey
        self.answers = answers
        self.department = department
        self.name = name
        self.on_close = on_close

        root.title("テスト結果")
        root.geometry("780x640")
        root.resizable(True, True)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._close)

        self._calculate_score()
        self._build()

    def _calculate_score(self):
        self.earned = 0
        self.total_possible = 0
        self.results = []  # [(question, answer, is_correct, points_earned)]

        for q in self.survey.questions:
            if q.type == "name_selector":
                continue
            answer = self.answers.get(q.id, "")
            correct = _is_correct(q, answer)
            pts_earned = q.points if correct else 0
            self.earned += pts_earned
            self.total_possible += q.points
            self.results.append((q, answer, correct, pts_earned))

        self.score_pct = (self.earned / self.total_possible * 100) if self.total_possible > 0 else 0
        self.passed = self.score_pct >= self.survey.pass_score

    def _build(self):
        # ヘッダー
        hdr_color = "#1B5E20" if self.passed else "#B71C1C"
        hdr = tk.Frame(self.root, bg=hdr_color, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        result_text = "✔ 合格" if self.passed else "✗ 不合格"
        tk.Label(hdr, text=f"テスト結果: {result_text}", font=FONT_LARGE,
                 bg=hdr_color, fg="white").pack(side="left", padx=16, pady=14)

        # スコアカード
        score_frame = tk.Frame(self.root, bg="#E8EAF6", pady=14)
        score_frame.pack(fill="x", padx=0)

        score_inner = tk.Frame(score_frame, bg="#E8EAF6")
        score_inner.pack()

        tk.Label(score_inner, text=f"{self.department} {self.name} さん",
                 font=FONT_MEDIUM, bg="#E8EAF6", fg=TEXT).pack()

        score_color = SUCCESS if self.passed else DANGER
        tk.Label(score_inner, text=f"{self.earned} / {self.total_possible} 点",
                 font=("Yu Gothic UI", 32, "bold"), bg="#E8EAF6", fg=score_color).pack(pady=4)
        tk.Label(score_inner, text=f"正答率: {self.score_pct:.1f}%  （合格ライン: {self.survey.pass_score}%）",
                 font=FONT_NORMAL, bg="#E8EAF6", fg=MUTED).pack()

        # 点数グラフ（円グラフ）
        if MATPLOTLIB_AVAILABLE:
            self._draw_score_pie(score_inner)

        # 設問別結果
        if self.survey.show_correct_after:
            tk.Label(self.root, text="設問別の結果", font=FONT_H2, bg=BG, fg=PRIMARY).pack(
                anchor="w", padx=16, pady=(10, 4))
            self._build_detail()

        # 閉じるボタン
        tk.Button(self.root, text="閉じる", font=FONT_MEDIUM, bg=PRIMARY, fg="white",
                  relief="flat", padx=20, pady=8, command=self._close).pack(pady=12)

    def _draw_score_pie(self, parent: tk.Frame):
        try:
            fig = Figure(figsize=(3, 2.2), dpi=90, facecolor="#E8EAF6")
            ax = fig.add_subplot(1, 1, 1)
            wrong = self.total_possible - self.earned
            colors = ["#2E7D32", "#EF9A9A"] if self.passed else ["#C62828", "#EF9A9A"]
            ax.pie([self.earned, wrong],
                   labels=[f"正解 {self.earned}点", f"不正解 {wrong}点"],
                   colors=colors, startangle=90,
                   autopct="%1.0f%%", textprops={"fontsize": 8})
            ax.set_facecolor("#E8EAF6")
            fig.tight_layout(pad=0.5)
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack()
        except Exception:
            pass

    def _build_detail(self):
        canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
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
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        inner.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        for i, (q, answer, is_corr, pts_earned) in enumerate(self.results, 1):
            bg_color = CORRECT if is_corr else INCORRECT
            card = tk.Frame(inner, bg=bg_color, relief="ridge", bd=1)
            card.pack(fill="x", padx=10, pady=4)

            # ヘッダー行
            hrow = tk.Frame(card, bg=bg_color)
            hrow.pack(fill="x", padx=10, pady=(8, 2))

            mark = "✔" if is_corr else "✗"
            mark_color = SUCCESS if is_corr else DANGER
            tk.Label(hrow, text=f"Q{i}. {mark}", font=FONT_MEDIUM, bg=bg_color, fg=mark_color).pack(side="left")
            tk.Label(hrow, text=f"{pts_earned}/{q.points}点", font=FONT_NORMAL, bg=bg_color, fg=TEXT).pack(side="right")

            # 設問文
            tk.Label(card, text=q.text, font=FONT_NORMAL, bg=bg_color, fg=TEXT,
                     wraplength=640, justify="left").pack(anchor="w", padx=10, pady=2)

            # 回答
            display_answer = answer.replace("|||", " / ") if answer else "（未回答）"
            ans_color = SUCCESS if is_corr else DANGER
            tk.Label(card, text=f"あなたの回答: {display_answer}", font=FONT_NORMAL,
                     bg=bg_color, fg=ans_color).pack(anchor="w", padx=10, pady=2)

            # 正解（不正解の場合のみ表示）
            if not is_corr and q.correct_answers:
                correct_display = " / ".join(q.correct_answers)
                tk.Label(card, text=f"正解: {correct_display}", font=FONT_NORMAL,
                         bg=bg_color, fg="#1B5E20").pack(anchor="w", padx=10, pady=(0, 8))
            else:
                tk.Frame(card, bg=bg_color, height=4).pack()

    def _close(self):
        if self.on_close:
            self.on_close()
        else:
            self.root.destroy()
