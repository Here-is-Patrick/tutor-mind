# TutorMind

> 课程：企业级应用软件设计与开发（AI 驱动的软件开发与 Agentic AI）  
> 课程代码：CS599 | 学期：2025-2026 春季  
> 方向：**方向一：Agentic AI 原生开发**

## 项目简介

TutorMind 是一个基于 **LangGraph 多智能体状态机** 的一对一智能学习辅导系统。系统通过多个专门化的 AI Agent 协同工作，为学生提供个性化的苏格拉底式教学体验，包括学生信息收集、知识库检索、递进式引导教学、实时搜索兜底等功能。系统支持**多轮对话**，LLM 能够基于完整对话历史进行上下文感知的连贯回复。

本项目从零开始基于多智能体架构设计，核心工作流由 LangGraph StateGraph 编排，各 Agent 通过共享状态（TutorState）协作完成教学任务。

## 核心技术要素

| 要素 | 实现说明 |
|------|----------|
| SDD 规格驱动开发 | Product Spec / Architecture Spec / API Spec 分层规格文档 |
| 状态管理与多步骤推理 | LangGraph StateGraph 编排完整教学工作流，MemorySaver 持久化状态 |
| 多智能体协作 | Orchestrator / InfoCollector / KnowledgeRetriever / SocraticTutor / SearchAgent 五角色协作 |
| 记忆机制 | 短期记忆（内存滑动窗口）+ 长期记忆（SQLite 持久化）+ 向量记忆（ChromaDB）+ LangGraph Checkpoint |
| 工具使用 / Function Calling | Tavily Search API 实时搜索兜底、学生画像 CRUD 工具 |
| 可观测性 | 结构化日志、健康检查端点、LLM 调用状态追踪 |
| 多轮对话 | 基于 LangChain BaseMessage 的标准消息序列，LLM 原生多轮上下文理解 |

## 技术栈

| 层级 | 技术 |
|------|------|
| AI IDE | Trae CN（课程指定） |
| LLM | 阿里云百炼 DashScope (通义千问系列) |
| Agent 框架 | LangGraph + LangChain |
| 后端框架 | FastAPI + Python 3.11+ |
| 向量数据库 | ChromaDB |
| 结构化存储 | SQLite |
| 实时搜索 | Tavily Search API |
| 前端 | React 18 + TypeScript + Tailwind CSS |
| 容器 | Docker + Docker Compose |
| 协议 | SSE 流式传输、REST API |

## 目录结构

```
tutor-mind/
├── docs/                           # 文档目录（预留）
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py             # FastAPI 入口
│   │   │   ├── config.py           # 配置管理（环境变量读取）
│   │   │   ├── agents/             # 多智能体实现
│   │   │   │   ├── orchestrator.py # 编排器：统一 LLM 调用、记忆管理、多轮对话消息转换
│   │   │   │   ├── info_collector.py   # 信息收集器：学生画像构建 + 资料更新意图识别
│   │   │   │   ├── knowledge_retriever.py  # 知识检索器：RAG 向量检索
│   │   │   │   ├── socratic_tutor.py   # 苏格拉底导师：递进式引导教学（支持多轮历史）
│   │   │   │   └── search_agent.py # 搜索代理：Tavily 实时搜索兜底（支持多轮历史）
│   │   │   ├── graph/              # LangGraph 状态机编排
│   │   │   │   ├── state.py        # TutorState 状态定义
│   │   │   │   └── workflow.py     # 多 Agent 工作流定义（含多轮消息构建）
│   │   │   ├── tools/              # 工具函数
│   │   │   │   ├── tavily_tool.py  # Tavily API 封装
│   │   │   │   ├── kb_search.py    # 知识库搜索工具
│   │   │   │   ├── foundation_check.py # 基础水平检测
│   │   │   │   └── student_profile.py  # 学生画像管理
│   │   │   ├── rag/                # RAG 实现
│   │   │   │   ├── embeddings.py   # DashScope Embedding 生成
│   │   │   │   ├── vector_store.py # ChromaDB 向量存储
│   │   │   │   └── retriever.py    # 检索器（嵌入+检索+过滤）
│   │   │   ├── memory/             # 记忆机制
│   │   │   │   ├── short_term.py   # 短期记忆：内存滑动窗口
│   │   │   │   └── long_term.py    # 长期记忆：SQLite 持久化
│   │   │   ├── models/             # 数据模型
│   │   │   │   ├── schemas.py      # Pydantic 模型
│   │   │   │   └── database.py     # SQLite 数据库操作
│   │   │   ├── api/                # API 路由
│   │   │   │   ├── chat.py         # 聊天 API（流式/非流式，加载历史消息到 State）
│   │   │   │   ├── student.py      # 学生信息管理
│   │   │   │   └── analytics.py    # 学习分析
│   │   │   └── crew/               # CrewAI 扩展（预留）
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── .env.example            # 环境变量模板
│   └── frontend/
│       └── src/
│           ├── App.tsx             # 主应用组件
│           ├── components/
│           │   ├── ChatPanel.tsx   # 聊天面板（流式消息、Markdown、公式渲染）
│           │   └── Sidebar.tsx     # 侧边栏（会话管理、学生信息）
│           ├── services/
│           │   └── api.ts          # API 调用封装
│           └── types.ts            # TypeScript 类型定义
├── docker-compose.yml
├── .gitignore
├── LICENSE
└── README.md
```

## 环境搭建

### 1. 依赖安装

**后端依赖：**

```bash
cd src/backend
pip install -r requirements.txt
```

**前端依赖：**

```bash
cd src/frontend
npm install
```

### 2. 环境变量配置

复制环境变量模板并填入你的 API Key：

```bash
cd src/backend
cp .env.example .env
```

编辑 `.env` 文件：

```env
# ── 阿里云百炼 DashScope ───────────────────────────────
# 获取地址：https://bailian.console.aliyun.com/
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# LLM 模型：qwen-turbo | qwen-plus | qwen-max
LLM_MODEL=qwen-plus

# Embedding 模型：text-embedding-v2 | text-embedding-v3
EMBEDDING_MODEL=text-embedding-v2

# ── Tavily Search ──────────────────────────────────────
# 获取地址：https://app.tavily.com/
TAVILY_API_KEY=your_tavily_api_key_here

# ── 应用配置 ───────────────────────────────────────────
DEBUG=false
HOST=0.0.0.0
PORT=8000

# ── ChromaDB ───────────────────────────────────────────
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=qa_embeddings

# ── SQLite ─────────────────────────────────────────────
SQLITE_PATH=./data/tutor_mind.db

# ── 检索配置 ───────────────────────────────────────────
SIMILARITY_THRESHOLD=0.75
TOP_K_RETRIEVAL=3

# ── 对话配置 ───────────────────────────────────────────
MAX_SHORT_TERM_MESSAGES=20

# ── CORS ───────────────────────────────────────────────
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

⚠️ **注意**：API Key 通过环境变量注入，严禁硬编码在代码中。

### 3. 启动步骤

**方式一：本地启动**

```bash
# 启动后端
cd src/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（新终端）
cd src/frontend
npm run dev
```

- 前端访问：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

**方式二：Docker 部署**

```bash
# 确保 .env 已配置
docker-compose up -d
```

- 前端访问：http://localhost:3000
- 后端 API：http://localhost:8000

## 项目状态

- [x] Proposal
- [x] MVP
- [ ] Final

## 系统架构

```
学生输入
    │
    ▼
check_student_info（检查学生信息完整性 + 检测资料更新意图）
    │
    ├── 信息不完整 / 检测到更新意图 ──→ collect_info（收集/更新信息）──→ END
    │
    └── 信息完整 ──→ search_knowledge_base（知识库检索）
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                KB 命中           KB 未命中
                    │               │
                    ▼               ▼
            socratic_teach    tavily_search（实时搜索）
            （苏格拉底引导，        │
             携带多轮历史）         ▼
                    │         generate_answer（生成答案，携带多轮历史）
                    │               │
                    └───────┬───────┘
                            ▼
                    save_conversation_turn
                            │
                    rebuild_short_term_memory
                            │
                            ▼
                      return final_reply
```

## 核心功能

- **学生信息收集**：自动检测缺失信息并礼貌追问，建立学生画像
- **资料更新识别**：通过关键词启发式识别用户更新个人信息的意图（如"我的基础薄弱"），自动路由到信息收集节点
- **知识库优先检索**：向量检索相似历史问题，复用教学路径
- **苏格拉底式引导**：递进式提问引导学生自行推导答案，支持基于完整对话历史的多轮引导
- **实时搜索兜底**：知识库未命中时调用 Tavily Search API
- **多轮对话**：基于 LangChain `BaseMessage` 标准消息序列，LLM 原生理解对话上下文，实现连贯的多轮交互
- **自适应教学风格**：根据学生基础水平调整回答难度和语言风格
- **流式响应**：SSE 实时流式输出，提升交互体验
- **公式渲染**：基于 KaTeX 的 LaTeX 数学公式渲染
- **会话管理**：支持多会话、删除会话、删除单条消息
- **用户隔离**：不同学生的知识库和会话历史完全隔离

## 开发路线图

- **v0.1 (MVP)**: 核心 Agent 功能 + 前端对话界面
- **v0.2**: 多轮对话支持 + 苏格拉底引导优化 + 学生画像完善
- **v0.3**: 学习分析 + Docker 部署
- **v0.4**: MCP 协议 + 云部署 + 可观测性

## 学术声明

- 本项目为 CS599 课程大作业，代码与文档均为原创。
- 引用外部开源项目或论文已在文档中标注来源。
- API Key 均通过环境变量注入，代码中无硬编码密钥。

## License

MIT
