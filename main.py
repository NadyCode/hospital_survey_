"""
病院向けオフライン・アンケートシステム
エントリーポイント
"""
import sys
import os
import tempfile

# アプリのルートをパスに追加（exe化後も動作するよう）
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # type: ignore
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

import tkinter as tk
from config import ensure_shared_folder, get_app_title

# ──────────────────────────────────────────────────────────────
# 二重起動防止
# ──────────────────────────────────────────────────────────────
_MUTEX_NAME = "HospitalSurveySystem_SingleInstance_v1"
_LOCK_FILE   = os.path.join(tempfile.gettempdir(), "hospital_survey_app.lock")
_instance_lock = None   # GC されないようモジュール変数で保持


def _show_already_running():
    """すでに起動中である旨のダイアログを表示して終了する。"""
    _r = tk.Tk()
    _r.withdraw()
    from tkinter import messagebox
    messagebox.showwarning(
        "多重起動エラー",
        "病院アンケートシステムはすでに起動しています。\n"
        "タスクバー（または画面）を確認してください。",
    )
    _r.destroy()
    sys.exit(1)


def _ensure_single_instance():
    """
    多重起動を防止する。2つ目以降の起動はエラーダイアログを出して終了。

    Windows : Named Mutex（プロセス終了・クラッシュ時に OS が自動解放）
    Linux/macOS: ロックファイル + fcntl（プロセス終了時に自動解放）
    """
    global _instance_lock

    if sys.platform == "win32":
        import ctypes
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        ERROR_ALREADY_EXISTS = 183
        if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            _show_already_running()  # noreturn
        _instance_lock = mutex  # プロセス生存中は保持し続ける
    else:
        import fcntl
        try:
            fh = open(_LOCK_FILE, "w")
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.write(str(os.getpid()))
            fh.flush()
            _instance_lock = fh   # ファイルハンドルを保持（GCで閉じると lock 解放）
        except (IOError, OSError):
            _show_already_running()  # noreturn


def main():
    ensure_shared_folder()

    # 共有フォルダに新しいバージョンがあれば更新して再起動（exe・Windows のみ）
    try:
        from utils.updater import check_and_apply_update
        if check_and_apply_update():
            sys.exit(0)
    except Exception:
        pass

    _ensure_single_instance()

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

    from views.styles import init_global_scroll
    init_global_scroll(root)

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
