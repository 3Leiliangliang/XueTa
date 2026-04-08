# XueTa

XueTa 是一个面向学习场景的 AI 学习助手项目，当前采用前后端分离架构：

- `Web/`：基于 `Vue 3 + Vite + Vue Router + Pinia + Tailwind CSS` 的前端界面
- `backend/`：基于 `FastAPI + SQLAlchemy + PostgreSQL` 的后端服务

项目围绕学习过程中的几个核心环节展开：翻译、问答、笔记整理、学习规划、知识库、练习生成、学习进度追踪，以及个性化学习桌面。当前仓库已经具备较完整的后端业务骨架，以及一套视觉风格统一的前端原型页面，适合作为 AI 学习平台的课程项目、毕业设计或后续产品化开发基础。

## 项目定位

XueTa 的目标不是做单点工具，而是尝试把学习闭环串起来：

1. 用户先设定学习目标与计划
2. 在学习过程中进行翻译、查资料、记笔记、问答
3. 把资料沉淀进知识库
4. 根据知识点生成练习并完成作答
5. 通过进度、掌握度和复习计划形成反馈

也就是说，XueTa 更强调“学习流程协同”而不是“单次 AI 对话”。

## 当前状态

当前仓库的实现状态可以概括为：

- 前端：已经完成首页、翻译、问答、笔记、学习桌面、学习规划、认证页、关于页等页面原型，交互和视觉结构较完整，但大多数页面仍以本地状态或静态数据驱动，尚未全面切换到真实后端 API。
- 后端：已经完成认证、规划、笔记、聊天、知识库、练习、进度、桌面布局、文件上传等模块的接口、模型和服务层，具备较强的业务扩展基础。
- AI 能力：当前部分能力仍属于“占位式”或“规则式”实现，例如聊天回复、练习生成、知识检索等，代码中已经为 `OpenAI / pgvector / Redis / LlamaIndex / Langfuse` 预留后续接入空间。

## 核心功能

### 前端侧

- 首页与产品介绍页
- 登录、注册、重置密码页面
- AI 翻译页面
- AI 问答页面
- 笔记整理页面
- 学习规划页面
- 学习桌面页面

### 后端侧

- 用户注册、密码登录、验证码登录、刷新 Token、登出
- 当前用户资料查询与更新
- 学习目标与学习任务管理
- 笔记本、笔记、待办、总结管理
- 聊天会话、消息、反馈记录
- 知识库、文档、切块、检索
- 练习集生成、提交作答、评分、错题沉淀
- 学习记录、知识掌握度、复习计划
- 桌面布局保存
- 文件上传、下载、删除

## 技术栈

### 前端

- Vue 3
- Vite
- Vue Router
- Pinia
- Tailwind CSS
- ESLint
- Vitest

### 后端

- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- pgvector
- Redis
- Pydantic Settings
- python-jose / passlib
- pytest

### AI 与扩展能力

- OpenAI
- LlamaIndex
- Langfuse
- SSE 流式响应能力预留

## 项目结构

```text
XueTa/
├─ Web/                         # 前端项目
│  ├─ src/
│  │  ├─ components/            # UI 组件、图标、首页组件等
│  │  ├─ router/                # 前端路由
│  │  ├─ views/                 # 页面视图
│  │  └─ main.js
│  ├─ package.json
│  └─ README.md
├─ backend/                     # 后端项目
│  ├─ app/
│  │  ├─ api/                   # 路由层
│  │  ├─ core/                  # 配置、数据库、日志、安全等
│  │  ├─ models/                # SQLAlchemy 数据模型
│  │  ├─ schemas/               # 请求/响应模型
│  │  ├─ services/              # 业务逻辑层
│  │  ├─ repositories/          # 预留的数据访问层
│  │  ├─ tasks/                 # 预留的后台任务层
│  │  └─ main.py                # FastAPI 应用入口
│  ├─ docs/
│  │  └─ database-schema.md     # 数据库设计文档
│  ├─ storage/                  # 本地文件存储目录
│  ├─ tests/
│  ├─ requirements.txt
│  ├─ .env.example
│  └─ README.md
└─ README.md
```

## 架构概览

```mermaid
graph LR
    A[浏览器前端 Web] --> B[FastAPI Backend]
    B --> C[(PostgreSQL)]
    B --> D[(Redis)]
    B --> E[Local Storage]
    B --> F[OpenAI / Embedding]
    B --> G[LlamaIndex / Langfuse]
```

说明：

- 当前业务主链路主要依赖 `FastAPI + PostgreSQL + Local Storage`
- `Redis / pgvector / LlamaIndex / Langfuse` 已在设计和依赖层预留，但尚未全部正式启用

## 安装与运行

### 环境要求

- Node.js：`^20.19.0` 或 `>=22.12.0`
- npm：建议使用随 Node 一起安装的较新版本
- Python：建议 `3.10+`
- PostgreSQL：建议本地创建 `xueta` 数据库
- Redis：本地可用实例即可

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd XueTa
```

### 2. 启动后端

### 2.1 创建虚拟环境

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

### 2.3 配置环境变量

```powershell
Copy-Item .env.example .env
```

或：

```bash
cp .env.example .env
```

然后根据本地环境修改 `backend/.env`。

### 2.4 准备数据库与 Redis

请确保：

- PostgreSQL 已启动
- 已创建数据库 `xueta`
- Redis 已启动

项目默认连接如下：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/xueta
REDIS_URL=redis://localhost:6379/0
```

### 2.5 启动后端服务

```bash
uvicorn app.main:app --reload
```

说明：

- 开发环境下，后端会在启动时执行 `Base.metadata.create_all()` 自动建表
- 当前尚未补齐 Alembic 迁移脚本，生产环境部署前建议补充数据库迁移方案

启动后可访问：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/api/v1/health`

### 3. 启动前端

```bash
cd Web
npm install
npm run dev
```

默认启动地址：

- `http://127.0.0.1:5173`

其他常用命令：

```bash
npm run build
npm run lint
npm run test:unit
```

### 4. 前后端联调建议

推荐的联调顺序：

1. `auth`
2. `planner`
3. `notes`
4. `chat`
5. `desktop + files`
6. `practice + progress`
7. `knowledge base`

这样可以先跑通账号体系和主业务流程，再逐步接入复杂的 AI 功能。

## 后端环境变量说明

以下是 `backend/.env.example` 中的主要配置项：

| 变量名 | 说明 | 默认值 |
| --- | --- | --- |
| `APP_NAME` | 应用名称 | `XueTa Backend` |
| `APP_ENV` | 运行环境 | `development` |
| `APP_VERSION` | 应用版本 | `0.1.0` |
| `API_V1_PREFIX` | API 路由前缀 | `/api/v1` |
| `SECRET_KEY` | JWT 签名密钥 | `replace-me-with-a-strong-secret` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 过期时间 | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 过期时间 | `14` |
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+psycopg://postgres:postgres@localhost:5432/xueta` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | 允许跨域的前端地址 | `["http://localhost:5173"]` |
| `OPENAI_API_KEY` | 大模型 API Key | 空 |
| `OPENAI_MODEL` | 默认聊天模型 | `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | 默认向量模型 | `text-embedding-3-small` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse 公钥 | 空 |
| `LANGFUSE_SECRET_KEY` | Langfuse 私钥 | 空 |
| `LANGFUSE_HOST` | Langfuse 服务地址 | `https://cloud.langfuse.com` |
| `LOCAL_STORAGE_PATH` | 本地文件存储目录 | `storage` |

## 设计思路

### 1. 以前后端分离承载多端扩展

学习助手类产品天然包含较多交互页面和业务模块。前端负责承载用户体验、信息组织和多页面流转，后端负责封装数据模型、权限、安全和 AI 业务逻辑。这样拆分有几个好处：

- 前端可以独立迭代交互原型
- 后端可以先沉淀统一的数据结构和接口规范
- 后续可以扩展移动端、小程序或桌面端，而不必重写业务逻辑

### 2. 以后端分层降低业务复杂度

后端目前基本采用以下分层：

- `api`：负责 HTTP 路由和入参绑定
- `schemas`：负责请求与响应结构
- `services`：负责核心业务逻辑
- `models`：负责 ORM 数据模型
- `core`：负责配置、数据库、安全、异常、日志

这种结构适合当前项目的原因在于：学习平台的领域对象很多，认证、计划、笔记、练习、知识库之间又存在较强关联。如果把逻辑全部堆在路由层，后续接入 AI 工作流时会非常难维护。把业务沉到 `services` 后，后续替换实现会更平滑。

### 3. 先打通业务闭环，再逐步增强 AI

这个项目的一个核心设计选择是：先把业务对象、数据结构、状态流转和基础 CRUD 打通，再逐步把“规则式占位实现”升级成“真实 AI 能力”。

当前已经体现出这种思路：

- 聊天模块已经有会话、消息、反馈结构，但回复内容仍是占位式教学回答
- 知识库模块已经有知识库、文档、切块和检索流程，但目前主要是关键词匹配，向量检索仍待接入
- 练习模块已经有生成、提交、评分、错题沉淀、掌握度更新，但题目生成和评分逻辑目前偏规则式

这样做的好处是：

- 可以先验证产品结构是否合理
- 可以先让前后端联调与数据库设计稳定下来
- 后续接入 OpenAI、Embedding、RAG、链路观测时，不需要推翻整体架构

### 4. 用“学习闭环”组织数据模型

数据库设计不是按技术模块切，而是尽量按学习行为切：

- 目标与任务，对应“我要学什么”
- 笔记与知识库，对应“我学到了什么”
- 问答与检索，对应“我卡在哪里”
- 练习、错题、掌握度、复习计划，对应“我是否真正掌握”

这意味着数据库表之间存在跨模块关联，但整体产品逻辑会更顺。项目里的 `database-schema.md` 也是围绕这个思路组织的。

### 5. 为后续 AI 能力预留扩展位

虽然当前 AI 相关能力还未全部正式接入，但设计上已经做了预留：

- `pgvector`：为知识块向量检索做准备
- `Redis`：为缓存和异步任务协同做准备
- `LlamaIndex`：为 RAG 工作流做准备
- `Langfuse`：为 Prompt、调用链和效果观测做准备
- `sse-starlette`：为流式输出做准备

这类预留让项目不会停留在“静态课程作业”层面，而是可以逐步演进成更完整的 AI 应用。

## 设计重难点

### 1. 多模块协同带来的领域复杂度

XueTa 不是单一的聊天机器人，而是把规划、笔记、资料、练习、进度统一到一个系统里。难点在于这些模块既要独立可用，又要能形成关联。例如练习结果要反哺掌握度，知识库文档又要服务于问答与复习。这对数据库设计和服务层边界划分要求比较高。

### 2. AI 能力接入不能破坏业务骨架

很多 AI 项目一开始就把逻辑直接写在调用模型的流程里，后期会很难维护。这个项目的难点在于，既要体现 AI 学习助手特色，又要避免“模型一换，整个系统重写”。因此目前采用了“先建业务骨架，再替换 AI 内核”的策略。

### 3. 知识库与检索链路的演进式设计

知识库模块的真正难点不只是上传文档，而是：

- 文档解析
- 内容切块
- Embedding 生成
- 向量召回
- 结果重排
- 引用来源展示

当前仓库已经完成了文档、切块和基础检索能力，但从关键词检索升级到高质量 RAG 仍然是后续最关键的技术演进点之一。

### 4. 练习、错题与进度的联动

练习系统的难点不只是“出题”，更是怎样把答题结果转成可追踪的学习数据。当前项目在提交练习后，会同步记录：

- 作答结果
- 每题反馈
- 错题本
- 学习记录
- 知识点掌握度
- 下次复习时间

这条链路是整个项目最有产品价值的部分之一，也是设计上比较容易牵一发动全身的地方。

### 5. 文件存储与用户隔离

文件上传和知识库接入涉及存储安全问题。当前后端在文件与存储路径处理上做了基础隔离：

- 文件按用户目录存储
- 下载与查询都受用户身份限制
- 本地路径会做解析校验，避免越界访问

虽然现在仍是本地存储方案，但这部分设计为后续迁移对象存储留下了空间。

### 6. 前后端成熟度不一致

当前仓库里，前端完成度更多体现在页面原型与交互组织，后端完成度更多体现在数据结构和业务 API。这种“前端偏展示、后端偏骨架”的阶段性不一致，是项目当前最现实的工程状态。

这既是难点，也是优势：

- 难点在于联调前仍需要补一轮真实接口接入
- 优势在于后续可以在不推翻视觉设计的情况下，把真实能力逐步填进去

## 已实现模块一览

| 模块 | 当前状态 |
| --- | --- |
| 认证 | 已完成注册、密码登录、验证码登录、刷新 Token、登出、忘记密码、重置密码 |
| 用户 | 已完成当前用户查询与资料更新 |
| 学习规划 | 已完成目标、任务 CRUD 和计划快照生成 |
| 笔记 | 已完成笔记本、笔记、待办、总结相关接口 |
| 聊天 | 已完成会话、消息、反馈的持久化，回复仍为占位式实现 |
| 知识库 | 已完成知识库、文档、切块、关键词检索 |
| 练习 | 已完成练习集生成、作答提交、评分、错题沉淀 |
| 进度 | 已完成学习记录、掌握度、复习计划 |
| 桌面布局 | 已完成布局保存、读取、列表、更新、删除 |
| 文件 | 已完成上传、列表、详情、下载、删除 |

## 后续建议

如果你准备继续完善这个项目，建议优先按以下顺序推进：

1. 为后端补齐 Alembic 迁移脚本
2. 把前端 `planning / note / qa / desktop` 等页面逐步切到真实 API
3. 为聊天模块接入真实大模型与流式输出
4. 为知识库接入 Embedding、pgvector 和 RAG 检索
5. 为练习生成与评分接入更强的 AI 链路
6. 接入 Redis 后台任务和 Langfuse 观测
7. 补充更多自动化测试

## 测试与校验

当前仓库中已经包含基础后端测试示例：

```bash
cd backend
pytest
```

前端可使用：

```bash
cd Web
npm run test:unit
```

## 适用场景

这个项目适合用于：

- 软件工程课程设计
- 毕业设计或创新创业项目原型
- AI 学习平台方向的继续开发
- 前后端分离与 AI 应用架构练习

## 说明

如果你只是想先预览界面效果，可以先单独运行前端；如果你想完整推进成可用系统，建议优先把后端环境、数据库和联调链路搭起来，再逐步补齐 AI 能力接入。
