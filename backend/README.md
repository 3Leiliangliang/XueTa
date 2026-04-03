# XueTa 后端

XueTa 后端是 XueTa AI 学习助手的 FastAPI 服务层，整体按照 v2 技术方案设计，核心技术栈包括：

- `FastAPI`：提供 HTTP API，后续可扩展 SSE 流式输出
- `PostgreSQL + pgvector`：同时承载业务数据和向量检索
- `Redis`：用于缓存和后台任务协调
- `LlamaIndex`：用于知识库索引与检索流程
- `Langfuse`：用于可观测性、Prompt 跟踪与效果分析

## 项目目标

后端围绕 AI 学习助手的核心场景进行设计：

- 用户认证与个人资料管理
- 学习目标、学习任务与进度追踪
- 笔记、总结与知识沉淀
- AI 问答与后续 RAG 检索增强
- 教材/讲义等知识库文档接入
- 练习生成、批改与错题沉淀
- 学习数据分析与复习计划
- 个性化学习桌面配置

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

### 4. 启动服务

```powershell
uvicorn app.main:app --reload
```

启动后可访问：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## 当前状态

目前后端已经具备以下能力：

- FastAPI 应用入口、统一路由注册和 CORS 中间件
- 开发环境下基于 SQLAlchemy Metadata 的自动建表
- 基于 JWT 的鉴权流程与 Bearer Token 保护接口
- 注册、密码登录、验证码登录、刷新 Token、登出、忘记密码、重置密码
- 当前用户查询与用户资料更新
- 学习规划模块的真实 CRUD：目标与任务
- 笔记模块的真实 CRUD：笔记本、笔记、待办、总结
- 问答模块的基础会话持久化：会话、消息、反馈
- 基础学习计划快照生成接口
- 首版 SQLAlchemy 数据模型
- 健康检查测试与数据库结构文档

以下模块目前仍是骨架，下一阶段继续实现：

- 问答模块的 SSE 流式输出
- 知识库文档入库与检索
- 练习生成与自动批改
- 学习进度分析与复习计划
- 桌面个性化与文件流转
- Alembic 迁移脚本

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
- `POST /api/v1/chat/messages/{message_id}/feedback`

## 模块说明

- `auth`：注册、登录、验证码、密码重置、Token 生命周期
- `users`：当前用户与资料维护
- `planner`：学习目标、学习任务、计划快照生成
- `notes`：笔记本、笔记、总结、待办
- `chat`：问答会话、消息记录、基础反馈
- `kb`：知识文档、检索、索引流程
- `practice`：练习生成、答题提交、批改
- `progress`：学习记录、掌握度、复习计划
- `desktop`：个性化桌面布局保存
- `files`：文件上传与元数据入口

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

1. 初始化 Alembic 并生成第一版迁移脚本。
2. 实现问答模块的 SSE 流式输出。
3. 接入知识库文档解析、切片与 pgvector 检索。
4. 实现练习生成、提交与批改。
5. 补齐学习进度统计与复习计划接口。
6. 开始把前端 `note` 和 `qa` 页面切换到真实 API。

## 与前端联调说明

当前前端中的 `planning` 页面已经最适合优先联调，因为后端规划模块 CRUD 已经可用。现在 `note` 页面和 `qa` 页面也已经具备可对接的基础接口，可以开始逐步替换本地 `ref` mock 数据。真正的流式回答与知识检索链路可以放在下一轮继续接入。
