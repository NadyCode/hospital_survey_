"""
起動時の自動更新

共有フォルダ内の更新配置フォルダ（既定: <共有フォルダ>/_app_update/）に
新しいバージョンの実行ファイルが置かれている場合、自動的に差し替える。

配置イメージ:
    <共有フォルダ>/_app_update/version.txt          … 例: 1.1.0
    <共有フォルダ>/_app_update/HospitalSurvey.exe    … 新しい実行ファイル

仕組み:
    1. version.txt のバージョンが現在より新しいか比較
    2. 新しければ、待機→差し替え→再起動を行う小さなバッチを生成
    3. バッチを起動し、本体は終了する（バッチが本体終了後に exe を上書きして再起動）

注意:
    - 実行ファイル化（PyInstaller）された Windows 環境でのみ動作する。
    - 開発時（スクリプト実行）や非対応OSでは何もしない。
"""
import os
import sys
import tempfile
import subprocess


def _parse_version(s: str):
    """'1.2.3' -> (1, 2, 3)。解析できなければ (0,)。"""
    try:
        return tuple(int(x) for x in str(s).strip().split("."))
    except Exception:
        return (0,)


def _read_shared_version(version_file: str) -> str:
    try:
        with open(version_file, "r", encoding="utf-8-sig") as f:
            return f.read().strip()
    except Exception:
        return ""


def is_update_available(shared_folder: str, current_version: str):
    """
    更新が利用可能なら (新バージョン文字列, 新exeパス) を、なければ None を返す。
    （OS・frozen の判定はしない。呼び出し側の check_and_apply_update で行う）
    """
    from config import UPDATE_DIR_NAME, UPDATE_VERSION_FILE, UPDATE_EXE_NAME
    update_dir = os.path.join(shared_folder, UPDATE_DIR_NAME)
    version_file = os.path.join(update_dir, UPDATE_VERSION_FILE)
    new_exe = os.path.join(update_dir, UPDATE_EXE_NAME)

    if not (os.path.isfile(version_file) and os.path.isfile(new_exe)):
        return None

    shared_version = _read_shared_version(version_file)
    if not shared_version:
        return None

    if _parse_version(shared_version) <= _parse_version(current_version):
        return None

    return shared_version, new_exe


def _build_updater_bat(new_exe: str, current_exe: str) -> str:
    """差し替え用バッチを一時フォルダに作成し、そのパスを返す。"""
    bat_path = os.path.join(tempfile.gettempdir(), "hospital_survey_update.bat")
    # 本体終了を待ってから上書き → 再起動。copy が失敗する間はリトライ。
    content = (
        "@echo off\r\n"
        "chcp 65001 >NUL\r\n"
        "timeout /t 2 /nobreak >NUL\r\n"
        ":retry\r\n"
        f'copy /Y "{new_exe}" "{current_exe}" >NUL 2>&1\r\n'
        "if errorlevel 1 (\r\n"
        "    timeout /t 1 /nobreak >NUL\r\n"
        "    goto retry\r\n"
        ")\r\n"
        f'start "" "{current_exe}"\r\n'
        'del "%~f0"\r\n'
    )
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(content)
    return bat_path


def check_and_apply_update() -> bool:
    """
    更新を確認し、必要なら更新プロセスを起動する。
    更新を開始した場合 True（呼び出し側はアプリを終了すべき）。
    更新不要・非対応環境では False。
    """
    # 実行ファイル化された Windows 環境のみ対象
    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return False

    try:
        from config import get_shared_folder, APP_VERSION
        result = is_update_available(get_shared_folder(), APP_VERSION)
        if not result:
            return False

        new_version, new_exe = result
        current_exe = sys.executable

        # ユーザーに通知
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk()
            r.withdraw()
            messagebox.showinfo(
                "アップデート",
                f"新しいバージョン {new_version} が見つかりました。\n"
                f"アプリを更新して再起動します。",
            )
            r.destroy()
        except Exception:
            pass

        bat = _build_updater_bat(new_exe, current_exe)
        # バッチをデタッチして起動
        subprocess.Popen(["cmd", "/c", bat],
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                         | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        return True
    except Exception:
        # 更新処理で問題が起きても通常起動を妨げない
        return False
