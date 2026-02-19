"""
アプリ共通スタイル定義
"""
import tkinter as tk
from tkinter import ttk

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
    """スクロール可能なフレームを作成。(canvas, inner_frame) を返す"""
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

    def _on_mousewheel(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)
    inner.bind("<MouseWheel>", _on_mousewheel)

    return canvas, inner, container


def make_separator(parent, **kwargs):
    sep = ttk.Separator(parent, orient="horizontal")
    sep.pack(fill="x", pady=6, **kwargs)
    return sep
