# 05｜API 接口说明

默认服务：`http://127.0.0.1:8000`；交互式文档：`/docs`。

## 健康、设置和首页

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/settings` | 模型和平台能力状态 |
| GET | `/api/dashboard` | 首页统计及最近记录 |

## 信息收件箱

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/inbox?status=PENDING&limit=100` | 列表 |
| POST | `/api/inbox/text` | 新增文本 |
| POST | `/api/inbox/upload` | multipart 文件上传 |
| GET | `/api/inbox/{id}` | 详情 |
| POST | `/api/inbox/{id}/organize` | AI 整理 |
| POST | `/api/inbox/{id}/to-knowledge` | 沉淀知识 |

文本示例：

```json
{"title":"客户沟通记录","text":"客户希望下周收到外贸网站报价方案。","source_type":"wechat_clip","source_name":"用户主动复制的微信聊天"}
```

上传字段：`file` 必填；`source_type`、`title` 可选。

## 知识中心

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/knowledge?q=外贸&limit=100` | 搜索 |
| POST | `/api/knowledge` | 新建 |
| GET | `/api/knowledge/{id}` | 详情和版本 |
| PUT | `/api/knowledge/{id}` | 更新并产生新版本 |
| POST | `/api/knowledge/ask` | 检索和问答 |

问答：`{"question":"我收集过哪些外贸获客建议？","limit":5}`。

## 内容中心

| Method | Path | 说明 |
|---|---|---|
| POST | `/api/content/generate` | 生成多平台草稿 |
| GET | `/api/content?status=DRAFT` | 列表 |
| GET | `/api/content/{id}` | 详情和发布记录 |
| PUT | `/api/content/{id}` | 编辑草稿 |
| POST | `/api/content/{id}/approve` | 审核通过 |
| POST | `/api/content/{id}/record-published` | 登记人工发布 |

生成请求示例：

```json
{
  "topic":"小微企业如何用 AI 做持续内容获客",
  "platforms":["xiaohongshu","douyin","wechat_official"],
  "knowledge_ids":[],
  "audience":"小微企业老板",
  "tone":"专业、可信、易懂"
}
```

支持平台键：`xiaohongshu`、`douyin`、`x`、`wechat_official`。

## 客户线索

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/leads` | 列表 |
| POST | `/api/leads` | 新增 |
| PATCH | `/api/leads/{id}` | 更新状态和备注 |

## 状态约束

- Inbox：PENDING → ORGANIZED → SAVED。
- Content：DRAFT → APPROVED → PUBLISHED。
- Lead：NEW → CONTACTED → QUALIFIED → WON/LOST。

## API 当前限制

无认证、无租户隔离、列表无游标分页（最大 200）、无官方平台 OAuth、无发布任务队列、无评论/私信 API、无正式删除/导出中心。仅本机使用。
