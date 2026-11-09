# AI Growth Workspace

本仓库包含本地单用户 MVP 和 V0.2 工作台重构。V0.2 的核心是减少人工操作：资料导入后后台自动整理，品牌和内容规则配置一次，后续内容生成自动复用。

## V0.2 新增

- AI 首页与全局任务输入框。
- 导入后后台自动整理、待审核知识候选。
- 品牌资料、客户画像、内容策略、平台规则、提示词管理。
- 配置驱动的多平台草稿生成与配置快照。
- 内容计划、自动化规则、执行历史和任务查询。
- 快捷键剪贴板剪藏 + 本地目录监控。

## 启动

~~~bash
./run.sh
~~~

Windows 使用 run.bat。打开 http://127.0.0.1:8000。

## 桌面助手

~~~bash
pip install -r requirements-desktop.txt
python desktop_helper/start_assistant.py
~~~

先复制选定文字，再按默认 Ctrl + Shift + Space。macOS 可尝试参数 --hotkey '<cmd>+<shift>+<space>'。详见 desktop_helper/README.md 和 docs/15-V0.2升级说明.md。

## 配置模型

在 .env 中设置 AI_BASE_URL、AI_API_KEY、AI_MODEL，修改后重启。模型密钥不通过前端保存。

## 重要边界

- 仅采集用户主动选择的微信文字、文件和本地资料；不读取微信内部数据库。
- 平台内容先生成草稿并人工审核；当前不宣称已接通小红书、抖音、X、公众号自动发布。
- V0.2 是本地单用户工作台，不要直接暴露公网。正式 SaaS 仍需认证、租户隔离、HTTPS、密钥管理、审计和安全测试。

## 测试

~~~bash
pip install -r requirements-dev.txt
pytest -q
~~~

V0.2 的交互和升级说明见 docs/15-V0.2升级说明.md。
