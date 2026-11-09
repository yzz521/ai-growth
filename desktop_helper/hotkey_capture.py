import argparse
import json
import urllib.request

def submit(api_url, text):
    compact = text.strip()
    title = next((line.strip() for line in compact.splitlines() if line.strip()), "快速剪藏")[:80]
    payload = json.dumps({
        "title": title,
        "text": compact[:100000],
        "source_type": "wechat_clip",
        "source_name": "desktop_hotkey_clipboard",
    }, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        api_url.rstrip("/") + "/api/inbox/text",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="用户主动触发的剪贴板剪藏快捷键")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--hotkey", default="<ctrl>+<shift>+<space>",
                        help="macOS 可尝试 <cmd>+<shift>+<space>")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    try:
        import pyperclip
    except ImportError as exc:
        raise SystemExit("缺少可选依赖，请执行 pip install -r requirements-desktop.txt") from exc

    def capture():
        try:
            text = pyperclip.paste()
            if not text or not text.strip():
                print("剪贴板没有文本，未提交。")
                return
            result = submit(args.api, text)
            print("已剪藏：", result.get("title", "资料"), "；AI 将在后台整理。")
        except Exception as exc:
            print("剪藏失败：", exc)

    if args.once:
        capture()
        return 0
    try:
        from pynput import keyboard
    except ImportError as exc:
        raise SystemExit("缺少 pynput，请执行 pip install -r requirements-desktop.txt") from exc

    print("快捷剪藏已启动，先复制文字，再按：", args.hotkey)
    print("按 Ctrl+C 退出。程序仅在快捷键触发时读取剪贴板。")
    with keyboard.GlobalHotKeys({args.hotkey: capture}) as listener:
        listener.join()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
