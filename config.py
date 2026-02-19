"""
アプリケーション設定
"""
import os
import json

# デフォルト設定ファイルパス
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")

DEFAULT_CONFIG = {
    "shared_folder": os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
    "admin_password": "admin1234",
    "app_title": "病院アンケートシステム",
    "app_version": "1.0.0",
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


def get_surveys_dir() -> str:
    d = os.path.join(get_shared_folder(), SURVEYS_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def ensure_shared_folder():
    os.makedirs(get_shared_folder(), exist_ok=True)
    os.makedirs(get_surveys_dir(), exist_ok=True)
