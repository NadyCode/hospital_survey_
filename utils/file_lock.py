"""
ファイル排他制御（簡易ロックファイル方式）
複数ユーザーが同時に共有フォルダへ書き込む際のデータ破損を防ぐ
"""
import os
import time
import contextlib

LOCK_TIMEOUT = 10   # 秒
LOCK_RETRY_INTERVAL = 0.1


class FileLockError(Exception):
    pass


@contextlib.contextmanager
def file_lock(target_path: str):
    """
    target_path に対応するロックファイルを作成し、排他的にアクセスする。
    with file_lock("answers.csv"):
        # ここで安全に読み書きできる
    """
    lock_path = target_path + ".lock"
    deadline = time.time() + LOCK_TIMEOUT
    acquired = False
    while time.time() < deadline:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            acquired = True
            break
        except FileExistsError:
            # 古いロックファイルを検出して削除（クラッシュ対策）
            try:
                mtime = os.path.getmtime(lock_path)
                if time.time() - mtime > LOCK_TIMEOUT * 2:
                    os.remove(lock_path)
            except OSError:
                pass
            time.sleep(LOCK_RETRY_INTERVAL)
    if not acquired:
        raise FileLockError(f"ロック取得タイムアウト: {lock_path}")
    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass
