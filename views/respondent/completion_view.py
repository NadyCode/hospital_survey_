"""
アンケート終了画面
テキスト・埋め込み画像・PDF を表示する
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from models.survey import Survey
from views.styles import (PRIMARY, BG, CARD_BG, FONT_LARGE, FONT_NORMAL, FONT_MEDIUM,
                           FONT_H2, FONT_SMALL, MUTED, SUCCESS, DANGER, WARNING, TEXT,
                           register_scrollable)

# Pillow が使えるかチェック（JPEG 等の広いフォーマット対応）
try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False

_COMPLETION_GREEN = "#1B5E20"
_COMPLETION_BG    = "#E8F5E9"


def _has_content(survey: Survey) -> bool:
    """終了画面に表示するコンテンツが設定されているか"""
    return bool(
        survey.completion_text
        or (survey.completion_image_path and os.path.exists(survey.completion_image_path))
        or survey.completion_pdf_path
    )


class CompletionWindow:
    """
    アンケート回答完了時に表示するウィンドウ。
    管理者が設定したテキスト・画像・PDF を表示する。
    """

    def __init__(self, root: tk.Toplevel, survey: Survey,
                 on_close: Optional[Callable] = None):
        self.root = root
        self.survey = survey
        self.on_close = on_close
        self._img_ref = None   # PhotoImage の GC 防止

        root.title("回答完了")
        root.resizable(True, True)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._close)

        self._build()

        # ウィンドウサイズ・中央配置
        root.update_idletasks()
        w, h = 660, 520
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ─────────────────────────────────────────────
    def _build(self):
        # ヘッダー
        hdr = tk.Frame(self.root, bg=_COMPLETION_GREEN, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="✔  回答が完了しました",
                 font=FONT_LARGE, bg=_COMPLETION_GREEN, fg="white").pack(
                     side="left", padx=20, pady=14)

        # スクロール可能コンテンツエリア
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
        register_scrollable(canvas)

        # ── コンテンツ ──

        # メッセージテキスト
        msg = self.survey.completion_text or "ご回答ありがとうございました。"
        msg_card = tk.Frame(inner, bg=_COMPLETION_BG, relief="flat")
        msg_card.pack(fill="x", padx=24, pady=(20, 10))
        tk.Label(msg_card, text=msg, font=FONT_MEDIUM, bg=_COMPLETION_BG, fg=TEXT,
                 wraplength=580, justify="left").pack(padx=18, pady=14)

        # 埋め込み画像
        img_path = self.survey.completion_image_path
        if img_path:
            self._show_image(inner, img_path)

        # PDF / テキストを開くボタン
        pdf_path = self.survey.completion_pdf_path
        if pdf_path:
            self._show_file_button(inner, pdf_path)

        # 閉じるボタン
        tk.Button(inner, text="閉じる", font=FONT_MEDIUM,
                  bg=_COMPLETION_GREEN, fg="white", relief="flat",
                  padx=28, pady=10, cursor="hand2",
                  command=self._close).pack(pady=(16, 24))

    # ─────────────────────────────────────────────
    def _show_image(self, parent: tk.Frame, path: str):
        """画像を内部に埋め込んで表示する"""
        if not os.path.exists(path):
            tk.Label(parent,
                     text=f"⚠ 画像ファイルが見つかりません:\n{path}",
                     font=FONT_NORMAL, bg=BG, fg=DANGER).pack(pady=8)
            return

        try:
            photo = self._load_photo(path)
        except Exception as e:
            tk.Label(parent,
                     text=f"⚠ 画像の読み込みエラー: {e}",
                     font=FONT_NORMAL, bg=BG, fg=DANGER).pack(pady=8)
            return

        if photo is None:
            ext = os.path.splitext(path)[1].upper()
            tk.Label(parent,
                     text=f"⚠ {ext} 形式を表示するには Pillow が必要です。\n"
                          f"   pip install Pillow  を実行してください。\n"
                          f"   ファイル: {os.path.basename(path)}",
                     font=FONT_NORMAL, bg=BG, fg=WARNING,
                     justify="left").pack(pady=8, padx=24, anchor="w")
            return

        self._img_ref = photo   # GC 防止
        frame = tk.Frame(parent, bg=BG)
        frame.pack(pady=10)
        tk.Label(frame, image=photo, bg=BG).pack()

    def _load_photo(self, path: str):
        """画像を tkinter で使える PhotoImage に変換する"""
        ext = os.path.splitext(path)[1].lower()
        if _PIL:
            img = Image.open(path)
            # 最大サイズに縮小（縦横比維持）
            img.thumbnail((600, 420), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            # Pillow なし: PNG / GIF のみネイティブ対応
            if ext in (".png", ".gif"):
                return tk.PhotoImage(file=path)
            return None

    def _show_file_button(self, parent: tk.Frame, path: str):
        """PDF / テキストを開くボタンを表示する"""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            icon, label = "📄", "PDF を開く"
        elif ext in (".txt", ".md"):
            icon, label = "📝", "テキストを開く"
        else:
            icon, label = "📎", "ファイルを開く"

        name = os.path.basename(path)
        exists = os.path.exists(path)

        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(pady=8)

        if exists:
            tk.Button(btn_frame, text=f"{icon}  {label}：{name}",
                      font=FONT_MEDIUM, bg=PRIMARY, fg="white", relief="flat",
                      padx=16, pady=8, cursor="hand2",
                      command=lambda: self._open_file(path)).pack()
        else:
            tk.Label(btn_frame,
                     text=f"⚠ ファイルが見つかりません:\n{path}",
                     font=FONT_NORMAL, bg=BG, fg=DANGER).pack()

    def _open_file(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開けませんでした:\n{e}")

    def _close(self):
        if self.on_close:
            self.on_close()
        else:
            self.root.destroy()
