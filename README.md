# AI Growth Workspace — 可运行 MVP

> 把零散信息变成知识，再用知识持续生产内容。首版面向个人本地使用和小范围试用，不宣称微信全量同步或四平台自动发布已实现。

## 当前能力

- 信息收件箱：粘贴用户主动选定的微信文字、文章摘录、会议笔记；上传 TXT/MD/CSV/JSON/可检索 PDF/DOCX。
- 本地桌面导入助手：监控 `data/dropbox/`，用户主动保存进去的文件自动导入。
- AI 整理：摘要、标签、事实候选、待办候选；未配置模型时使用明确标记的本地模板。
- 知识中心：从收件箱沉淀知识、关键词检索、知识问答、版本记录。
- 内容中心：基于选定知识生成小红书、抖音、X、微信公众号草稿。
- 内容审核和发布记录：编辑、审核通过、复制正文、人工发布后登记链接。
- 客户线索：登记客户、来源、需求和跟进状态。
- SQLite 本地数据、附件和 ZIP 备份。

## 当前不支持

1. 不读取微信加密数据库、不注入微信进程、不模拟登录、不静默抓取聊天。
2. 不自动登录或自动发布小红书、抖音、X、公众号；当前统一采用人工发布和链接登记。
3. 当前知识检索是关键词检索基线，不是向量 RAG；不含 OCR，扫描版 PDF 无法直接提取。
4. 当前无账号登录、多租户、团队权限、云同步、计费及公网安全能力。

## 环境要求

Python 3.10+（建议 3.11/3.12），macOS/Linux/Windows。可选 OpenAI-compatible Chat Completions 模型服务。

## 启动

macOS / Linux：

```bash
unzip ai-growth-workspace.zip
cd ai-growth-workspace
chmod +x run.sh
./run.sh
```

Windows：

```bat
cd ai-growth-workspace
run.bat
```

首次启动脚本创建 `.venv`、安装 requirements、复制 `.env.example` 为 `.env`，默认在 `127.0.0.1:8000` 启动。打开：

- 工作台：<http://127.0.0.1:8000>
- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

如果当前环境无法访问 PyPI，可在联网环境提前下载 wheel，再使用 `pip install --no-index --find-links <wheel目录> -r requirements.txt`。

## 配置模型

编辑根目录 `.env`：

```env
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=替换为自己的密钥
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=60
```

`AI_BASE_URL` 必须是兼容 OpenAI Chat Completions 的 API 根地址，程序请求 `/chat/completions`。不同服务商的模型名称、鉴权和结构化输出能力可能不同，需要按供应商文档配置。

**隐私提醒：** 配置远程模型后，用户提交给 AI 整理、问答和内容生成的文本片段会发送到所配置服务商。导入客户聊天、合同、电话等资料前，先确认有权处理，并核对模型服务商的数据用途和留存政策。不要把 `.env` 提交到 Git。

## 桌面助手

另开终端运行：

```bash
python desktop_helper/watch_folder.py
```

将用户主动导出、选定且有权处理的文件放进 `data/dropbox/`。成功导入后移动到 `processed/`。

主动保存一段文字：

```bash
python desktop_helper/capture_text.py "客户沟通记录" --text "客户希望下周收到报价方案。"
```

macOS 剪贴板示例：

```bash
pbpaste | python desktop_helper/capture_text.py "微信剪藏"
```

然后由 watch_folder 导入。该助手不读取微信客户端或内部数据。

## 测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

## 数据与备份

- `data/app.db`：SQLite 数据库。
- `data/uploads/`：上传原文件。
- `data/dropbox/`：桌面助手导入目录。
- `data/dropbox/processed/`：已导入文件。
- `data/backups/`：备份包。

备份：`python scripts/backup.py`。恢复前停止服务、备份当前目录，再按 `docs/06-部署与运行.md` 恢复数据库和附件。

## 文档阅读顺序

1. `docs/00-产品边界与决策.md`
2. `docs/01-PRD.md`
3. `docs/03-技术架构.md`
4. `docs/04-数据库设计.md`
5. `docs/06-部署与运行.md`
6. `docs/11-MVP验收清单.md`
7. `docs/12-升级路线图.md`

## 生产环境警告

当前服务默认绑定 `127.0.0.1`。**不要直接部署公网或提供多个用户使用。** 公网化前必须实现认证、租户隔离、HTTPS、密钥管理、限流、审计、数据导出/删除、备份恢复和安全测试，详见 `docs/09-安全与隐私.md`。
