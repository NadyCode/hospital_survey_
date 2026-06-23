"""
集計・グラフ表示タブ＆ウィンドウ
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from config import get_surveys_dir, get_shared_folder, get_data_path, MASTER_USER_FILE
from models.survey import Survey
from models.user import load_master_users
from utils.data_manager import (aggregate_answers, load_answers, get_answered_users,
                                export_answers_csv, get_answer_departments,
                                department_response_rates)
from views.styles import (PRIMARY, BG, CARD_BG, FONT_LARGE, FONT_NORMAL, FONT_MEDIUM,
                           FONT_H2, MUTED, SUCCESS, DANGER, FONT_SMALL, BORDER, TEXT)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
    # 日本語フォント設定
    _jp_fonts = ["Yu Gothic", "MS Gothic", "Hiragino Sans", "IPAexGothic",
                 "Noto Sans CJK JP", "TakaoGothic", "VL Gothic"]
    for _f in _jp_fonts:
        if any(_f.lower() in ff.lower() for ff in [f.name for f in fm.fontManager.ttflist]):
            plt.rcParams["font.family"] = _f
            break
    else:
        plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
except ImportError:
    MATPLOTLIB_AVAILABLE = False


COLORS = ["#1565C0", "#42A5F5", "#2E7D32", "#66BB6A", "#F57F17", "#FFCA28",
          "#C62828", "#EF9A9A", "#6A1B9A", "#CE93D8", "#00838F", "#80DEEA",
          "#E65100", "#FFCC80", "#37474F", "#90A4AE"]


class AggregatorTab:
    """管理者ダッシュボード内の集計タブ"""
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self._build()

    def _build(self):
        # アンケート選択
        top = tk.Frame(self.parent, bg=BG, pady=8)
        top.pack(fill="x", padx=16)
        tk.Label(top, text="アンケートを選択:", font=FONT_NORMAL, bg=BG).pack(side="left")
        self.survey_var = tk.StringVar()
        self.survey_combo = ttk.Combobox(top, textvariable=self.survey_var,
                                         font=FONT_NORMAL, width=40, state="readonly")
        self.survey_combo.pack(side="left", padx=8)
        self.survey_combo.bind("<<ComboboxSelected>>", lambda e: self._load_survey())
        tk.Button(top, text="🔄 更新", font=FONT_NORMAL, relief="flat",
                  padx=10, command=self._refresh_survey_list).pack(side="left")

        self._survey_map = {}
        self._refresh_survey_list()

        # コンテンツはここに後から追加
        self.content_frame = tk.Frame(self.parent, bg=BG)
        self.content_frame.pack(fill="both", expand=True)
        tk.Label(self.content_frame, text="アンケートを選択してください",
                 font=FONT_LARGE, bg=BG, fg=MUTED).pack(expand=True)

    def _refresh_survey_list(self):
        self._survey_map = {}
        survey_dir = get_surveys_dir()
        names = []
        for fname in sorted(os.listdir(survey_dir)):
            if fname.endswith(".json"):
                try:
                    s = Survey.load(os.path.join(survey_dir, fname))
                    label = f"{s.title} ({fname})"
                    self._survey_map[label] = (s, fname)
                    names.append(label)
                except Exception:
                    pass
        self.survey_combo["values"] = names

    def _load_survey(self):
        label = self.survey_var.get()
        if label not in self._survey_map:
            return
        survey, _ = self._survey_map[label]
        for w in self.content_frame.winfo_children():
            w.destroy()
        AggregatorContent(self.content_frame, survey)


class AggregatorWindow:
    """アンケート管理から開く集計ウィンドウ"""
    def __init__(self, root: tk.Toplevel, survey: Survey):
        self.root = root
        root.title(f"集計 - {survey.title}")
        root.geometry("1060x740")
        root.resizable(True, True)
        root.configure(bg=BG)
        AggregatorContent(root, survey)


class AggregatorContent:
    ALL_LABEL = "全体（すべての所属）"

    def __init__(self, parent: tk.Widget, survey: Survey):
        self.survey = survey
        self.parent = parent
        self._dept_filter = None     # None = 全体
        self._chart_figures = []
        self._build()

    def _build(self):
        # ツールバー
        tb = tk.Frame(self.parent, bg=BG, pady=6)
        tb.pack(fill="x", padx=12)
        tk.Label(tb, text=f"📊 {self.survey.title}", font=FONT_H2, bg=BG, fg=PRIMARY).pack(side="left")
        tk.Button(tb, text="📥 回答CSVをエクスポート", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=4, command=self._export_csv).pack(side="right", padx=4)
        tk.Button(tb, text="🖼️ グラフを画像保存", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=4, command=self._export_charts).pack(side="right", padx=4)

        # 所属（部署）フィルタ
        filter_bar = tk.Frame(self.parent, bg="#E3F2FD")
        filter_bar.pack(fill="x", padx=12, pady=(0, 4))
        tk.Label(filter_bar, text="🔎 所属で絞り込み:", font=FONT_NORMAL, bg="#E3F2FD").pack(
            side="left", padx=(8, 4), pady=6)
        depts = self._available_departments()
        self._dept_var = tk.StringVar(value=self.ALL_LABEL)
        self._dept_combo = ttk.Combobox(filter_bar, textvariable=self._dept_var,
                                        values=[self.ALL_LABEL] + depts,
                                        state="readonly", font=FONT_NORMAL, width=24)
        self._dept_combo.pack(side="left", pady=6)
        self._dept_combo.bind("<<ComboboxSelected>>", lambda e: self._on_dept_filter_change())
        tk.Label(filter_bar, text="（全体／所属別を切り替えて分析できます）",
                 font=FONT_SMALL, bg="#E3F2FD", fg=MUTED).pack(side="left", padx=8)

        # タブ
        nb = ttk.Notebook(self.parent)
        nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # 集計・グラフタブ
        tab_agg = ttk.Frame(nb)
        nb.add(tab_agg, text="  📊 集計・グラフ  ")
        # 中身は再描画できるようコンテナに格納
        self._agg_container = tk.Frame(tab_agg, bg=BG)
        self._agg_container.pack(fill="both", expand=True)
        self._render_aggregate()

        # 未回答者タブ
        tab_missing = ttk.Frame(nb)
        nb.add(tab_missing, text="  👤 回答状況  ")
        self._build_missing_tab(tab_missing)

        # 回答一覧タブ
        tab_raw = ttk.Frame(nb)
        nb.add(tab_raw, text="  📋 回答一覧  ")
        self._build_raw_tab(tab_raw)

    # ─────────────────── 所属フィルタ ───────────────────
    def _available_departments(self):
        """マスター＋回答データに含まれる部署の一覧"""
        depts = []
        for u in load_master_users(get_data_path(MASTER_USER_FILE)):
            if u.department not in depts:
                depts.append(u.department)
        for d in get_answer_departments(get_shared_folder(), self.survey.id):
            if d not in depts:
                depts.append(d)
        return depts

    def _on_dept_filter_change(self):
        sel = self._dept_var.get()
        self._dept_filter = None if sel == self.ALL_LABEL else sel
        self._render_aggregate()

    # ─────────────────── 集計・グラフ ───────────────────
    def _render_aggregate(self):
        # コンテナをクリアして再描画
        for w in self._agg_container.winfo_children():
            w.destroy()
        parent = self._agg_container

        agg = aggregate_answers(get_shared_folder(), self.survey.id,
                                self.survey.questions, department=self._dept_filter)

        # 絞り込み状態の見出し
        scope = "全体" if self._dept_filter is None else f"所属「{self._dept_filter}」"
        head = tk.Frame(parent, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text=f"集計対象: {scope}", font=FONT_NORMAL, bg=BG,
                 fg=PRIMARY).pack(anchor="w", padx=12, pady=(6, 0))

        has_data = any(agg.get(q.id, {}).get("total", 0) > 0 for q in self.survey.questions)
        if not has_data:
            tk.Label(parent, text="該当する回答データがありません",
                     font=FONT_LARGE, bg=BG, fg=MUTED).pack(expand=True)
            return

        # スクロール
        canvas_outer = tk.Canvas(parent, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas_outer.yview)
        canvas_outer.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas_outer.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas_outer, bg=BG)
        win_id = canvas_outer.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: (
            canvas_outer.configure(scrollregion=canvas_outer.bbox("all")),
            canvas_outer.itemconfig(win_id, width=canvas_outer.winfo_width())
        ))
        canvas_outer.bind("<Configure>", lambda e: canvas_outer.itemconfig(win_id, width=e.width))
        from views.styles import register_scrollable
        register_scrollable(canvas_outer)

        self._chart_figures = []

        for qi, q in enumerate(self.survey.questions, 1):
            qid = q.id
            if qid not in agg:
                continue
            data = agg[qid]
            qtype = data["type"]
            total = data.get("total", 0)

            card = tk.Frame(inner, bg=CARD_BG, relief="ridge", bd=1)
            card.pack(fill="x", padx=10, pady=6)

            # 設問タイトル
            tk.Label(card, text=f"Q{qi}. {data['text']}", font=FONT_MEDIUM,
                     bg=CARD_BG, fg=PRIMARY, wraplength=700, justify="left").pack(
                         anchor="w", padx=12, pady=(10, 4))
            tk.Label(card, text=f"回答数: {total} 件", font=FONT_SMALL, bg=CARD_BG, fg=MUTED).pack(
                anchor="w", padx=12)

            if qtype == "name_selector":
                # 部署・氏名を聞く設問は「所属別 回答率」を表示する
                tk.Label(card, text="所属別 回答率", font=FONT_NORMAL, bg=CARD_BG,
                         fg="#00695C").pack(anchor="w", padx=12, pady=(2, 0))
                rate_frame = tk.Frame(card, bg=CARD_BG)
                rate_frame.pack(fill="x", padx=12, pady=8)
                self._draw_rate_section(rate_frame)

            elif qtype in ("radio", "checkbox", "dropdown", "scale"):
                counts = data.get("counts", {})
                chart_frame = tk.Frame(card, bg=CARD_BG)
                chart_frame.pack(fill="x", padx=12, pady=8)

                if MATPLOTLIB_AVAILABLE and counts:
                    self._draw_chart(chart_frame, data, qtype)
                else:
                    # テキスト表示
                    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
                        pct = v / total * 100 if total else 0
                        row = tk.Frame(chart_frame, bg=CARD_BG)
                        row.pack(fill="x", pady=1)
                        tk.Label(row, text=f"{k}", font=FONT_NORMAL, bg=CARD_BG, width=24, anchor="w").pack(side="left")
                        bar_frame = tk.Frame(row, bg=CARD_BG, height=18)
                        bar_frame.pack(side="left", fill="x", expand=True)
                        bar_fill = tk.Frame(bar_frame, bg=PRIMARY, width=max(4, int(pct * 3)), height=18)
                        bar_fill.place(x=0, y=0)
                        tk.Label(row, text=f"{v} ({pct:.1f}%)", font=FONT_SMALL, bg=CARD_BG, width=12).pack(side="left")

                if qtype == "scale":
                    tk.Label(card, text=f"平均値: {data.get('average', 0):.2f}",
                             font=FONT_MEDIUM, bg=CARD_BG, fg=SUCCESS).pack(anchor="w", padx=12, pady=4)

            elif qtype in ("text", "textarea"):
                vals = data.get("values", [])
                list_frame = tk.Frame(card, bg=CARD_BG)
                list_frame.pack(fill="x", padx=12, pady=4)
                txt = tk.Text(list_frame, font=FONT_NORMAL, height=min(len(vals) + 1, 8),
                              relief="solid", bd=1, state="normal", wrap="word")
                txt.pack(fill="x")
                for i, v in enumerate(vals, 1):
                    txt.insert("end", f"{i}. {v}\n")
                txt.config(state="disabled")

    def _draw_chart(self, parent: tk.Frame, data: dict, qtype: str):
        counts = data.get("counts", {})
        options = data.get("options", list(counts.keys()))
        # 選択肢の順序を維持
        keys = [o for o in options if o in counts] + \
               [k for k in counts if k not in options]
        values = [counts.get(k, 0) for k in keys]
        total = sum(values) or 1

        fig = Figure(figsize=(8, 3.2), dpi=90, facecolor=CARD_BG)
        self._chart_figures.append(fig)

        ax_bar = fig.add_subplot(1, 2, 1)
        ax_pie = fig.add_subplot(1, 2, 2)

        colors = [COLORS[i % len(COLORS)] for i in range(len(keys))]

        # 棒グラフ
        bars = ax_bar.barh(keys, values, color=colors, edgecolor="white")
        ax_bar.set_xlabel("回答数", fontsize=9)
        ax_bar.set_title("棒グラフ", fontsize=10)
        ax_bar.tick_params(labelsize=9)
        for bar, v in zip(bars, values):
            pct = v / total * 100
            ax_bar.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                        f" {v} ({pct:.1f}%)", va="center", fontsize=8)
        ax_bar.set_facecolor(CARD_BG)

        # 円グラフ
        if any(v > 0 for v in values):
            wedges, texts, autotexts = ax_pie.pie(
                values, labels=None, autopct="%1.1f%%",
                colors=colors, startangle=90,
                wedgeprops=dict(edgecolor="white"))
            for at in autotexts:
                at.set_fontsize(8)
            ax_pie.set_title("円グラフ", fontsize=10)
            ax_pie.legend(wedges, keys, loc="lower center", bbox_to_anchor=(0.5, -0.25),
                          ncol=2, fontsize=7)
        else:
            ax_pie.text(0.5, 0.5, "データなし", ha="center", va="center")

        fig.tight_layout(pad=1.5)

        chart_canvas = FigureCanvasTkAgg(fig, master=parent)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(fill="x")

    def _draw_rate_section(self, parent: tk.Frame):
        """所属別の回答率を描画する（②）"""
        master = load_master_users(get_data_path(MASTER_USER_FILE))
        rates = department_response_rates(get_shared_folder(), self.survey.id, master)

        # 所属フィルタ中はその部署のみ表示
        if self._dept_filter:
            rates = {d: v for d, v in rates.items() if d == self._dept_filter}

        if not rates:
            tk.Label(parent, text="職員マスターまたは回答データがありません。",
                     font=FONT_NORMAL, bg=CARD_BG, fg=MUTED).pack(anchor="w")
            return

        depts = sorted(rates.keys())

        if MATPLOTLIB_AVAILABLE:
            fig = Figure(figsize=(8, max(2.2, 0.5 * len(depts) + 1.2)), dpi=90, facecolor=CARD_BG)
            self._chart_figures.append(fig)
            ax = fig.add_subplot(1, 1, 1)
            values = [rates[d]["rate"] for d in depts]
            colors = [COLORS[i % len(COLORS)] for i in range(len(depts))]
            bars = ax.barh(depts, values, color=colors, edgecolor="white")
            ax.set_xlim(0, 100)
            ax.set_xlabel("回答率 (%)", fontsize=9)
            ax.set_title("所属別 回答率", fontsize=10)
            ax.tick_params(labelsize=9)
            for bar, d in zip(bars, depts):
                info = rates[d]
                ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                        f" {info['rate']:.1f}%  ({info['answered']}/{info['total']}名)",
                        va="center", fontsize=8)
            ax.set_facecolor(CARD_BG)
            fig.tight_layout(pad=1.2)
            cv = FigureCanvasTkAgg(fig, master=parent)
            cv.draw()
            cv.get_tk_widget().pack(fill="x")
        else:
            for d in depts:
                info = rates[d]
                row = tk.Frame(parent, bg=CARD_BG)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=d, font=FONT_NORMAL, bg=CARD_BG, width=18, anchor="w").pack(side="left")
                bar_frame = tk.Frame(row, bg="#ECEFF1", height=18)
                bar_frame.pack(side="left", fill="x", expand=True, padx=4)
                fill = tk.Frame(bar_frame, bg=SUCCESS, width=max(2, int(info["rate"] * 2)), height=18)
                fill.place(x=0, y=0)
                tk.Label(row, text=f"{info['rate']:.1f}% ({info['answered']}/{info['total']}名)",
                         font=FONT_SMALL, bg=CARD_BG, width=18).pack(side="left")

    # ─────────────────── 回答状況 ───────────────────
    def _build_missing_tab(self, parent: ttk.Frame):
        toolbar = tk.Frame(parent, bg=BG, pady=6)
        toolbar.pack(fill="x", padx=12)
        tk.Label(toolbar, text="職員マスターと照合した回答状況", font=FONT_NORMAL, bg=BG, fg=MUTED).pack(side="left")
        tk.Button(toolbar, text="🔄 更新", font=FONT_NORMAL, relief="flat",
                  padx=10, pady=4, command=lambda: self._refresh_missing(tree)).pack(side="right")

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        cols = ("部署", "氏名", "状態", "回答日時")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        tree.tag_configure("answered", background="#C8E6C9")
        tree.tag_configure("missing", background="#FFCDD2")

        self._refresh_missing(tree)

    def _refresh_missing(self, tree: ttk.Treeview):
        tree.delete(*tree.get_children())
        users = load_master_users(get_data_path(MASTER_USER_FILE))
        answered = {(r["部署"], r["氏名"]): r["回答日時"]
                    for r in get_answered_users(get_shared_folder(), self.survey.id)}
        for u in users:
            key = (u.department, u.name)
            if key in answered:
                tree.insert("", "end", values=(u.department, u.name, "✔ 回答済", answered[key]),
                            tags=("answered",))
            else:
                tree.insert("", "end", values=(u.department, u.name, "✗ 未回答", ""),
                            tags=("missing",))

    # ─────────────────── 回答一覧 ───────────────────
    def _build_raw_tab(self, parent: ttk.Frame):
        answers = load_answers(get_shared_folder(), self.survey.id)
        if not answers:
            tk.Label(parent, text="回答データがありません", font=FONT_LARGE, bg=BG, fg=MUTED).pack(expand=True)
            return

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        cols = list(answers[0].keys()) if answers else []
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for col in cols:
            short = col if len(col) <= 12 else col[:10] + "…"
            tree.heading(col, text=short)
            tree.column(col, width=max(80, min(200, len(col) * 12)))

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        for row in answers:
            tree.insert("", "end", values=[row.get(c, "") for c in cols])

    # ─────────────────── エクスポート ───────────────────
    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"answers_{self.survey.id}.csv")
        if not path:
            return
        ok = export_answers_csv(get_shared_folder(), self.survey.id, path)
        if ok:
            messagebox.showinfo("エクスポート完了", f"保存しました:\n{path}")
        else:
            messagebox.showwarning("データなし", "エクスポートするデータがありません。")

    def _export_charts(self):
        if not MATPLOTLIB_AVAILABLE or not self._chart_figures:
            messagebox.showwarning("注意", "グラフデータがありません。")
            return
        folder = filedialog.askdirectory(title="グラフ画像の保存フォルダを選択")
        if not folder:
            return
        for i, fig in enumerate(self._chart_figures, 1):
            path = os.path.join(folder, f"chart_q{i}.png")
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=CARD_BG)
        messagebox.showinfo("保存完了", f"{len(self._chart_figures)} 枚のグラフを保存しました。\n{folder}")


def get_data_path(filename: str) -> str:
    from config import get_data_path as _gdp
    return _gdp(filename)
