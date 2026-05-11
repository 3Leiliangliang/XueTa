# XueTa 后端

XueTa 后端是 XueTa AI 学习助手的 FastAPI 服务层，当前以“先打通业务闭环、再接入更强 AI 链路”为主线推进。当前项目已经具备认证、学习规划、笔记、聊天会话、知识库、练习、学习进度、桌面布局和文件上传等核心接口。

## 核心技术栈

- `FastAPI`：提供 HTTP API，已支持首版 SSE 流式输出
- `SQLAlchemy 2.x`：统一 ORM 与数据访问层
- `PostgreSQL + pgvector`：业务数据与向量检索的目标存储方案
- `Redis`：缓存与后台任务协调的预留基础设施
- `LlamaIndex`：知识库索引 / 检索流程的预留能力
- `Langfuse`：Prompt、链路与效果观测的预留能力

说明：当前 `pgvector / Redis / LlamaIndex / Langfuse` 已完成依赖与模型层准备，但真正的向量检索、链路观测和异步任务协作仍会在下一阶段继续接入。

## 项目目标

后端围绕 AI 学习助手的核心场景进行设计：

- 用户认证与个人资料管理
- 学习目标、学习任务与进度追踪
- 笔记、总结与知识沉淀
- AI 问答与后续 RAG 检索增强
- 教材 / 讲义等知识库文档接入
- 练习生成、批改与错题沉淀
- 学习数据分析与复习计划
- 个性化学习桌面配置与文件流转

## 目录结构

```text
backend/
  app/
    api/
      v1/
    core/
    models/
    repositories/
    schemas/
    services/
    tasks/
    utils/
    main.py
  alembic/
  docs/
    database-schema.md
  storage/
  tests/
  .env.example
  requirements.txt
```

## 快速开始

### 1. 创建虚拟环境

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 配置环境变量

```powershell
Copy-Item .env.example .env
```

至少需要修改以下配置：

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY`

If `OPENAI_API_KEY` is configured, chat replies and note summaries will prefer a real model.
When chat requests fail with a configured key, the API now returns a clear model-configuration error (instead of silently returning placeholder text).

可选配置：

- `OPENAI_BASE_URL`：OpenAI 兼容网关地址（例如第三方兼容服务）
- `OPENAI_TIMEOUT_SECONDS`：模型请求超时时间（秒）
- `RUN_MIGRATIONS_ON_STARTUP=true`：启动服务时自动执行 Alembic 升级
- `AUTO_CREATE_TABLES=false`：在已使用迁移的环境中关闭开发模式下的 `create_all()` 兜底

### 4. 启动服务

```powershell
uvicorn app.main:app --reload
```

启动后可访问：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Database Migrations

Run the current baseline migration from `backend/` with:

If you want the app to apply migrations automatically on startup, set `RUN_MIGRATIONS_ON_STARTUP=true`.

```powershell
python -m alembic -c alembic.ini upgrade head
```

Create a new migration with:

```powershell
python -m alembic -c alembic.ini revision -m "your_migration_name"
```

Current baseline revision:

- `alembic/versions/20260407_0001_baseline_schema.py`

## 当前状态

目前后端已经具备以下能力：

- FastAPI 应用入口、统一路由注册和 CORS 中间件
- 开发环境下保留基于 SQLAlchemy Metadata 的自动建表能力（便于本地快速启动）
- 基于 JWT 的鉴权流程与 Bearer Token 保护接口
- 注册、密码登录、验证码登录、刷新 Token、登出、忘记密码、重置密码
- 当前用户查询与用户资料更新
- 学习规划模块的真实 CRUD：目标、任务、状态更新与计划快照生成
- 笔记模块的真实 CRUD：笔记本、笔记、待办、总结
- 问答模块的真实基础能力：会话、消息、反馈与首版 SSE 流式输出
- 桌面布局模块的真实 CRUD：按名称获取 / 保存布局、布局列表、详情、更新、删除
- 文件模块的真实 CRUD：上传、列表、详情、下载、删除
- 学习进度模块的真实能力：学习概览、学习记录、知识掌握度、复习计划
- 练习模块的首版业务闭环：题集生成、题集详情、提交作答、评分结果、错题沉淀
- 知识库模块的首版业务闭环：知识库 CRUD、文档 CRUD、自动切块、关键词检索
- Alembic 已初始化，并提供首版 baseline 迁移脚本
- 首版 SQLAlchemy 数据模型、健康检查测试与数据库结构文档

以下部分仍在下一阶段继续增强：

- 聊天与笔记总结继续增强模型质量与提示词效果
- 知识库接入更完整的文档解析、Embedding 与 pgvector 检索
- 练习生成与批改进一步接入更强的 AI 生成 / 评估链路
- Redis 任务调度、Langfuse 观测链路、LlamaIndex 工作流正式接入

## 已可用接口

### 认证模块

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login/password`
- `POST /api/v1/auth/login/code`
- `POST /api/v1/auth/code/send`
- `POST /api/v1/auth/password/forgot`
- `POST /api/v1/auth/password/reset`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`

### 学习规划模块

- `GET /api/v1/planner/goals`
- `POST /api/v1/planner/goals`
- `GET /api/v1/planner/goals/{goal_id}`
- `PATCH /api/v1/planner/goals/{goal_id}`
- `DELETE /api/v1/planner/goals/{goal_id}`
- `GET /api/v1/planner/tasks`
- `POST /api/v1/planner/tasks`
- `GET /api/v1/planner/tasks/{task_id}`
- `PATCH /api/v1/planner/tasks/{task_id}`
- `PATCH /api/v1/planner/tasks/{task_id}/status`
- `DELETE /api/v1/planner/tasks/{task_id}`
- `POST /api/v1/planner/generate`

### 笔记模块

- `GET /api/v1/notes/notebooks`
- `POST /api/v1/notes/notebooks`
- `GET /api/v1/notes/notebooks/{notebook_id}`
- `PATCH /api/v1/notes/notebooks/{notebook_id}`
- `DELETE /api/v1/notes/notebooks/{notebook_id}`
- `GET /api/v1/notes`
- `POST /api/v1/notes`
- `GET /api/v1/notes/{note_id}`
- `PATCH /api/v1/notes/{note_id}`
- `DELETE /api/v1/notes/{note_id}`
- `GET /api/v1/notes/{note_id}/todos`
- `POST /api/v1/notes/{note_id}/todos`
- `PATCH /api/v1/notes/todos/{todo_id}`
- `DELETE /api/v1/notes/todos/{todo_id}`
- `POST /api/v1/notes/{note_id}/summarize`

### 问答模块

- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}`
- `PATCH /api/v1/chat/sessions/{session_id}`
- `DELETE /api/v1/chat/sessions/{session_id}`
- `GET /api/v1/chat/sessions/{session_id}/messages`
- `POST /api/v1/chat/sessions/{session_id}/messages`
- `POST /api/v1/chat/sessions/{session_id}/messages/stream`
- `POST /api/v1/chat/messages/{message_id}/feedback`

### 知识库模块

- `GET /api/v1/kb/bases`
- `POST /api/v1/kb/bases`
- `GET /api/v1/kb/bases/{base_id}`
- `PATCH /api/v1/kb/bases/{base_id}`
- `DELETE /api/v1/kb/bases/{base_id}`
- `GET /api/v1/kb/documents`
- `POST /api/v1/kb/documents`
- `GET /api/v1/kb/documents/{document_id}`
- `PATCH /api/v1/kb/documents/{document_id}`
- `DELETE /api/v1/kb/documents/{document_id}`
- `GET /api/v1/kb/documents/{document_id}/chunks`
- `POST /api/v1/kb/retrieve`

### 练习模块

- `POST /api/v1/practice/generate`
- `GET /api/v1/practice/sets`
- `GET /api/v1/practice/sets/{set_id}`
- `GET /api/v1/practice/sets/{set_id}/attempts`
- `POST /api/v1/practice/sets/{set_id}/attempts`
- `GET /api/v1/practice/attempts/{attempt_id}`
- `GET /api/v1/practice/wrong-questions`

### 学习进度模块

- `GET /api/v1/progress/overview`
- `GET /api/v1/progress/mastery`
- `POST /api/v1/progress/mastery`
- `GET /api/v1/progress/records`
- `POST /api/v1/progress/records`
- `GET /api/v1/progress/reviews`
- `POST /api/v1/progress/reviews`
- `PATCH /api/v1/progress/reviews/{review_id}`

### 桌面布局模块

- `GET /api/v1/desktop/layout`
- `PUT /api/v1/desktop/layout`
- `GET /api/v1/desktop/layouts`
- `POST /api/v1/desktop/layouts`
- `GET /api/v1/desktop/layouts/{layout_id}`
- `PATCH /api/v1/desktop/layouts/{layout_id}`
- `DELETE /api/v1/desktop/layouts/{layout_id}`

### 文件模块

- `GET /api/v1/files`
- `POST /api/v1/files/upload`
- `GET /api/v1/files/{file_id}`
- `GET /api/v1/files/{file_id}/download`
- `DELETE /api/v1/files/{file_id}`

## 模块说明

- `auth`：注册、登录、验证码、密码重置、Token 生命周期
- `users`：当前用户与资料维护
- `planner`：学习目标、学习任务、计划快照生成
- `notes`：笔记本、笔记、总结、待办
- `chat`：同步 / 流式问答会话、消息记录、基础反馈
- `kb`：知识库、文档、切块、关键词检索
- `practice`：练习生成、作答提交、评分与错题沉淀
- `progress`：学习记录、掌握度、复习计划与概览统计
- `desktop`：个性化桌面布局保存
- `files`：文件上传、下载与元数据管理

## 数据库设计

详细表结构请查看 [docs/database-schema.md](./docs/database-schema.md)。

当前模型层主要覆盖：

- 用户与认证相关表
- 学习规划与笔记相关表
- 问答与 RAG 相关表
- 练习与学习进度相关表
- 桌面配置与收藏表
- 文件元数据表

## 建议的下一步

1. 接入知识库文档解析、切片 Embedding 与 pgvector 检索。
2. 将聊天流式回答与练习批改升级到更强的 AI 链路。
3. 补充 Redis 后台任务、Langfuse 观测与 LlamaIndex 工作流。
4. 开始把前端 `planning`、`note`、`qa`、`desktop` 等页面逐步切到真实 API。

## 与前端联调说明

当前后端已经具备较完整的业务骨架，前端适合按以下顺序联调：

1. `auth` + `planner`
2. `notes` + `chat`
3. `desktop` + `files`
4. `practice` + `progress`
5. `kb`

真正的流式回答、向量检索和更强的 AI 生成链路，可以放在下一轮继续接入。
