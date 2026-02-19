"""
アクセスログ管理
アプリ起動時に「日時・端末名・IPアドレス・モード」をCSVに記録する
"""
import os
import csv
import socket
import datetime
from utils.file_lock import file_lock


def get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "UNKNOWN"


def get_ip_address() -> str:
    try:
        # LAN側IPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "0.0.0.0"


def write_access_log(log_path: str, mode: str, extra: str = ""):
    """
    アクセスログを追記する
    mode: "admin" or "respondent"
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = get_hostname()
    ip = get_ip_address()
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    with file_lock(log_path):
        file_exists = os.path.exists(log_path)
        with open(log_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["日時", "端末名", "IPアドレス", "モード", "備考"])
            writer.writerow([now, hostname, ip, mode, extra])


def read_access_logs(log_path: str) -> list:
    """アクセスログを読み込む"""
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)
