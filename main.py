"""
病院向けオフライン・アンケートシステム
エントリーポイント
"""
import sys
import os

# アプリのルートをパスに追加（exe化後も動作するよう）
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # type: ignore
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

import tkinter as tk
from config import ensure_shared_folder, get_app_title


def main():
    ensure_shared_folder()

    root = tk.Tk()
    root.title(get_app_title())

    # DPI対応（Windows高解像度ディスプレイ）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    # アイコン設定（存在する場合）
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    from views.main_window import MainWindow
    app = MainWindow(root)

    # ウィンドウを画面中央に配置
    root.update_idletasks()
    w, h = 800, 560
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    root.mainloop()


if __name__ == "__main__":
    main()
