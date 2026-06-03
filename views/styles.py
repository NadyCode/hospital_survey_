"""
アプリ共通スタイル定義
"""
import tkinter as tk
from tkinter import ttk
import sys

# ────────────────────────────────────────────────────────────────
# グローバルマウスホイールスクロール管理
# ────────────────────────────────────────────────────────────────
_scroll_canvases: list = []

# ネイティブスクロールを持つウィジェット（これらには介入しない）
_NATIVE_SCROLL_TYPES = (tk.Listbox, tk.Text)


def register_scrollable(canvas: tk.Canvas):
    """スクロール対象の canvas を登録する。"""
    _scroll_canvases.append(canvas)

    def _on_destroy(e):
        if canvas in _scroll_canvases:
            _scroll_canvases.remove(canvas)

    canvas.bind("<Destroy>", _on_destroy, add="+")


def init_global_scroll(root: tk.Tk):
    """
    ルートウィンドウに bind_all でグローバルスクロールを登録する。
    main.py で一度だけ呼ぶ。
    マウス座標から登録済み canvas を特定してスクロールするため、
    子ウィジェット上でも確実に動作する。
    """

    def _do_scroll(canvas: tk.Canvas, units: int):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(units, "units")
        except Exception:
            pass

    def _find_canvas(rx: int, ry: int) -> tk.Canvas | None:
        """マウス座標 (root 絶対座標) が重なる最前面の canvas を返す"""
        found = None
        for c in _scroll_canvases:
            try:
                if not c.winfo_exists():
                    continue
                cx, cy = c.winfo_rootx(), c.winfo_rooty()
                cw, ch = c.winfo_width(), c.winfo_height()
                if cx <= rx <= cx + cw and cy <= ry <= cy + ch:
                    found = c  # 後勝ち（リスト後方 = より新しく開いたウィンドウ）
            except Exception:
                pass
        return found

    # Windows / macOS: <MouseWheel>
    def _on_wheel_win(event):
        if isinstance(event.widget, _NATIVE_SCROLL_TYPES):
            return  # Listbox や Text の独自スクロールを妨げない
        c = _find_canvas(event.x_root, event.y_root)
        if c:
            _do_scroll(c, -1 * (event.delta // 120))
            return "break"

    # Linux: Button-4 (up) / Button-5 (down)
    def _on_wheel_up(event):
        if isinstance(event.widget, _NATIVE_SCROLL_TYPES):
            return
        c = _find_canvas(event.x_root, event.y_root)
        if c:
            _do_scroll(c, -1)
            return "break"

    def _on_wheel_down(event):
        if isinstance(event.widget, _NATIVE_SCROLL_TYPES):
            return
        c = _find_canvas(event.x_root, event.y_root)
        if c:
            _do_scroll(c, 1)
            return "break"

    root.bind_all("<MouseWheel>", _on_wheel_win, add="+")
    root.bind_all("<Button-4>", _on_wheel_up, add="+")
    root.bind_all("<Button-5>", _on_wheel_down, add="+")

# カラーパレット
PRIMARY   = "#1565C0"   # 濃い青
SECONDARY = "#42A5F5"   # 薄い青
SUCCESS   = "#2E7D32"   # 緑
WARNING   = "#F57F17"   # 黄
DANGER    = "#C62828"   # 赤
BG        = "#F5F7FA"   # 背景
CARD_BG   = "#FFFFFF"   # カード背景
TEXT      = "#212121"   # テキスト
MUTED     = "#757575"   # サブテキスト
BORDER    = "#E0E0E0"   # ボーダー
CORRECT   = "#C8E6C9"   # 正解（薄緑）
INCORRECT = "#FFCDD2"   # 不正解（薄赤）

# フォント
FONT_FAMILY = "Yu Gothic UI" if True else "TkDefaultFont"
FONT_SMALL   = (FONT_FAMILY, 9)
FONT_NORMAL  = (FONT_FAMILY, 11)
FONT_MEDIUM  = (FONT_FAMILY, 12)
FONT_LARGE   = (FONT_FAMILY, 14, "bold")
FONT_TITLE   = (FONT_FAMILY, 18, "bold")
FONT_H2      = (FONT_FAMILY, 15, "bold")


def apply_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", font=FONT_NORMAL, background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD_BG, relief="flat")
    style.configure("TLabel", background=BG, foreground=TEXT, font=FONT_NORMAL)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT)
    style.configure("Title.TLabel", font=FONT_TITLE, foreground=PRIMARY, background=BG)
    style.configure("H2.TLabel", font=FONT_H2, foreground=PRIMARY, background=CARD_BG)
    style.configure("Muted.TLabel", foreground=MUTED, background=CARD_BG)
    style.configure("Required.TLabel", foreground=DANGER, background=CARD_BG)

    # ボタン
    style.configure("TButton", font=FONT_NORMAL, padding=(10, 6))
    style.configure("Primary.TButton", background=PRIMARY, foreground="white", font=FONT_MEDIUM)
    style.map("Primary.TButton", background=[("active", SECONDARY)])
    style.configure("Success.TButton", background=SUCCESS, foreground="white", font=FONT_MEDIUM)
    style.map("Success.TButton", background=[("active", "#388E3C")])
    style.configure("Danger.TButton", background=DANGER, foreground="white", font=FONT_MEDIUM)
    style.map("Danger.TButton", background=[("active", "#B71C1C")])
    style.configure("Warning.TButton", background=WARNING, foreground="white", font=FONT_MEDIUM)
    style.map("Warning.TButton", background=[("active", "#E65100")])

    # ノートブック（タブ）
    style.configure("TNotebook", background=BG)
    style.configure("TNotebook.Tab", font=FONT_MEDIUM, padding=(12, 6))
    style.map("TNotebook.Tab", background=[("selected", PRIMARY)], foreground=[("selected", "white")])

    # スクロールバー
    style.configure("TScrollbar", background=BORDER)

    # エントリー
    style.configure("TEntry", fieldbackground=CARD_BG)

    # ラジオ・チェック
    style.configure("TRadiobutton", background=CARD_BG, font=FONT_NORMAL)
    style.configure("TCheckbutton", background=CARD_BG, font=FONT_NORMAL)

    # ツリービュー
    style.configure("Treeview", font=FONT_NORMAL, rowheight=26)
    style.configure("Treeview.Heading", font=FONT_MEDIUM, background=PRIMARY, foreground="white")
    style.map("Treeview", background=[("selected", SECONDARY)])

    # Combobox
    style.configure("TCombobox", font=FONT_NORMAL)

    # Progressbar
    style.configure("Horizontal.TProgressbar", troughcolor=BORDER, background=SUCCESS)


def scrollable_frame(parent, **kwargs) -> tuple:
    """スクロール可能なフレームを作成。(canvas, inner_frame, container) を返す"""
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True, **kwargs)

    canvas = tk.Canvas(container, bg=CARD_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas, style="Card.TFrame")

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    register_scrollable(canvas)

    return canvas, inner, container


def make_separator(parent, **kwargs):
    sep = ttk.Separator(parent, orient="horizontal")
    sep.pack(fill="x", pady=6, **kwargs)
    return sep
