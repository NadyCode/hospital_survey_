"""
アプリケーション設定
"""
import os
import sys
import json

# ─── バージョン（リリース時にここを更新してビルドし直す） ───────────────
APP_VERSION = "1.0.0"

# ─── 設定ファイルの場所 ──────────────────────────────────────────────
# exe 化時: exe と同じフォルダ（ユーザーが設定を保持できるよう外部ファイル）
# 開発時 : スクリプトと同じフォルダ
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_APP_DIR, "app_config.json")

DEFAULT_CONFIG = {
    "shared_folder": os.path.join(_APP_DIR, "data"),
    "admin_password": "admin1234",
    "app_title": "病院アンケートシステム",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # マージ（新キーがあれば追加）
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# グローバル設定オブジェクト
APP_CONFIG = load_config()


def get_shared_folder() -> str:
    return APP_CONFIG["shared_folder"]


def get_admin_password() -> str:
    return APP_CONFIG["admin_password"]


def get_app_title() -> str:
    return APP_CONFIG["app_title"]


def get_data_path(filename: str) -> str:
    return os.path.join(get_shared_folder(), filename)


# 固定ファイル名
MASTER_USER_FILE = "master_user.csv"
ANSWERS_FILE = "answers.csv"
ACCESS_LOG_FILE = "access_log.csv"
SURVEYS_DIR = "surveys"

# ───── 自動更新 ─────
UPDATE_DIR_NAME = "_app_update"       # 共有フォルダ内の更新配置フォルダ
UPDATE_VERSION_FILE = "version.txt"   # 最新バージョンを記載するファイル
UPDATE_EXE_NAME = "HospitalSurvey.exe"  # 配布する実行ファイル名


def get_update_dir() -> str:
    return os.path.join(get_shared_folder(), UPDATE_DIR_NAME)


def get_surveys_dir() -> str:
    d = os.path.join(get_shared_folder(), SURVEYS_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def ensure_shared_folder():
    os.makedirs(get_shared_folder(), exist_ok=True)
    os.makedirs(get_surveys_dir(), exist_ok=True)

