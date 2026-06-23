"""
build.bat / deploy_update.bat から呼び出されるヘルパー

使い方:
  python _update_version.py --read            -> config.py の APP_VERSION を表示
  python _update_version.py 1.2.0             -> config.py の APP_VERSION を 1.2.0 に書き換え
  python _update_version.py --shared-folder   -> app_config.json の shared_folder を表示
"""
import json
import os
import re
import sys


def cmd_read_version():
    txt = open("config.py", encoding="utf-8").read()
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', txt)
    print(m.group(1) if m else "0.0.0")


def cmd_set_version(version):
    path = "config.py"
    txt = open(path, encoding="utf-8").read()
    out = re.sub(r'APP_VERSION\s*=\s*"[^"]+"', f'APP_VERSION = "{version}"', txt)
    if out == txt:
        print("[WARN] config.py に APP_VERSION が見つかりませんでした。", file=sys.stderr)
        sys.exit(1)
    open(path, "w", encoding="utf-8").write(out)
    print(f"[VER] config.py の APP_VERSION を {version} に更新しました。")


def cmd_shared_folder():
    if os.path.exists("app_config.json"):
        d = json.load(open("app_config.json", encoding="utf-8"))
        print(d.get("shared_folder", "data"))
    else:
        print("data")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "--read":
        cmd_read_version()
    elif args[0] == "--shared-folder":
        cmd_shared_folder()
    else:
        cmd_set_version(args[0].strip())


if __name__ == "__main__":
    main()
