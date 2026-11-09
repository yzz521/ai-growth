# 桌面助手

## 文件夹监控

启动工作台后运行：

~~~bash
python desktop_helper/watch_folder.py
~~~

把你主动导出、选定且有权处理的文件放到 data/dropbox/。成功导入后移动到 processed/，服务端会按自动整理偏好处理。

## 快捷键剪藏

安装可选依赖：

~~~bash
pip install -r requirements-desktop.txt
~~~

然后启动：

~~~bash
python desktop_helper/start_assistant.py
~~~

默认快捷键 Ctrl + Shift + Space。macOS 可以尝试：

~~~bash
python desktop_helper/start_assistant.py --hotkey '<cmd>+<shift>+<space>'
~~~

操作：先复制微信中自己选择的文字，再按快捷键。程序只在热键触发时读取当前剪贴板，将文字提交到本地工作台；服务端按配置自动整理。

macOS 如需系统输入监听权限，请在系统隐私与安全设置中给终端/Python 授予相应权限。

## 安全边界

桌面助手不读取微信内部数据库、不注入微信、不模拟登录，不会在后台持续监控剪贴板。只处理用户主动触发的文本和放入监控目录的文件。
