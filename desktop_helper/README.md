# 本地桌面导入助手

这是用户主动采集工具，不是微信插件：不访问微信进程、内部数据库、账号令牌或私有协议。

1. 启动主服务：`./run.sh` / `run.bat`。
2. 另开终端运行：`python desktop_helper/watch_folder.py`。
3. 把用户主动保存的 TXT、MD、CSV、JSON、可检索 PDF、DOCX 文件放入 `data/dropbox/`。
4. 成功导入后移动至 `processed/`。

主动保存文本示例：

```bash
python desktop_helper/capture_text.py "客户沟通记录" --text "客户希望下周收到报价方案。"
pbpaste | python desktop_helper/capture_text.py "微信剪藏"
```

未来桌面壳可使用 Tauri/Electron 增加托盘和主动快捷键；剪贴板权限读取必须明确告知并由用户触发，不做后台静默监听。
