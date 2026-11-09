import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description="启动目录监控和主动剪藏快捷键")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--hotkey", default="<ctrl>+<shift>+<space>")
    args = parser.parse_args()
    watcher = subprocess.Popen([
        sys.executable, str(ROOT / "desktop_helper" / "watch_folder.py"), "--api", args.api
    ])
    try:
        subprocess.run([
            sys.executable, str(ROOT / "desktop_helper" / "hotkey_capture.py"),
            "--api", args.api, "--hotkey", args.hotkey
        ], check=False)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.terminate()
        try:
            watcher.wait(timeout=5)
        except subprocess.TimeoutExpired:
            watcher.kill()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
