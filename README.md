# TutorMind

## 项目简介

TutorMind 是一个基于 **LangGraph 多智能体状态机** 的一对一智能学习辅导系统。系统通过多个专门化的 AI Agent 协同工作，为学生提供个性化的苏格拉底式教学体验，包括学生信息收集、知识库检索、递进式引导教学、实时搜索兜底等功能。

## 方向

**方向一：Agentic AI 原生开发**

本项目从零开始基于多智能体架构设计，核心工作流由 LangGraph StateGraph 编排，各 Agent 通过共享状态（TutorState）协作完成教学任务。

## 技术栈

| 层级 | 技术 |
|------|------|
| AI IDE | Trae CN |
| LLM | 阿里云百炼 DashScope (通义千问系列) |
| 状态编排 | LangGraph (StateGraph) |
| 后端框架 | FastAPI + Python 3.11+ |
| 向量数据库 | ChromaDB |
| 结构化存储 | SQLite |
| 实时搜索 | Tavily Search API |
| 前端 | React 18 + TypeScript + Tailwind CSS |
| 容器 | Docker + Docker Compose |

## 目录结构

```
tutor-mind/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理（环境变量读取）
│   │   ├── agents/                 # 多智能体实现
│   │   │   ├── orchestrator.py     # 编排器：统一 LLM 调用、记忆管理
│   │   │   ├── info_collector.py   # 信息收集器：学生画像构建
│   │   │   ├── knowledge_retriever.py  # 知识检索器：RAG 向量检索
│   │   │   ├── socratic_tutor.py   # 苏格拉底导师：递进式引导教学
│   │   │   └── search_agent.py     # 搜索代理：Tavily 实时搜索兜底
│   │   ├── graph/                  # LangGraph 状态机编排
│   │   │   ├── state.py            # TutorState 状态定义
│   │   │   └── workflow.py         # 多 Agent 工作流定义
│   │   ├── tools/                  # 工具函数
│   │   │   ├── tavily_tool.py      # Tavily API 封装
│   │   │   ├── kb_search.py        # 知识库搜索工具
│   │   │   ├── foundation_check.py # 基础水平检测
│   │   │   └── student_profile.py  # 学生画像管理
│   │   ├── rag/                    # RAG 实现
│   │   │   ├── embeddings.py       # DashScope Embedding 生成
│   │   │   ├── vector_store.py     # ChromaDB 向量存储
│   │   │   └── retriever.py        # 检索器（嵌入+检索+过滤）
│   │   ├── memory/                 # 记忆机制
│   │   │   ├── short_term.py       # 短期记忆：内存滑动窗口
│   │   │   └── long_term.py        # 长期记忆：SQLite 持久化
│   │   ├── models/                 # 数据模型
│   │   │   ├── schemas.py          # Pydantic 模型
│   │   │   └── database.py         # SQLite 数据库操作
│   │   ├── api/                    # API 路由
│   │   │   ├── chat.py             # 聊天 API（流式/非流式）
│   │   │   ├── student.py          # 学生信息管理
│   │   │   └── analytics.py        # 学习分析
│   │   └── crew/                   # CrewAI 扩展（预留）
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example                # 环境变量模板
├── frontend/
│   └── src/
│       ├── App.tsx                 # 主应用组件
│       ├── components/
│       │   ├── ChatPanel.tsx       # 聊天面板（流式消息、Markdown、公式渲染）
│       │   └── Sidebar.tsx         # 侧边栏（会话管理、学生信息）
│       ├── services/
│       │   └── api.ts              # API 调用封装
│       └── types.ts                # TypeScript 类型定义
├── docker-compose.yml
└── README.md
```

## 环境搭建

### 1. 依赖安装

**后端依赖：**

```bash
cd backend
pip install -r requirements.txt
```

**前端依赖：**

```bash
cd frontend
npm install
```

### 2. 环境变量配置

复制环境变量模板并填入你的 API Key：

```bash
cd backend
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
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（新终端）
cd frontend
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
check_student_info（检查学生信息完整性）
    │
    ├── 信息不完整 ──→ collect_info（收集信息）──→ END
    │
    └── 信息完整 ──→ search_knowledge_base（知识库检索）
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                KB 命中           KB 未命中
                    │               │
                    ▼               ▼
            socratic_teach    tavily_search（实时搜索）
            （苏格拉底引导）          │
                    │               ▼
                    │         generate_answer（生成答案）
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
- **知识库优先检索**：向量检索相似历史问题，复用教学路径
- **苏格拉底式引导**：递进式提问引导学生自行推导答案
- **实时搜索兜底**：知识库未命中时调用 Tavily Search API
- **自适应教学风格**：根据学生基础水平调整回答难度和语言风格
- **流式响应**：SSE 实时流式输出，提升交互体验
- **公式渲染**：基于 KaTeX 的 LaTeX 数学公式渲染
- **会话管理**：支持多会话、删除会话、删除单条消息
- **用户隔离**：不同学生的知识库和会话历史完全隔离

## 开发路线图

- **v0.1 (MVP)**: 核心 Agent 功能 + 前端对话界面
- **v0.2**: 苏格拉底引导优化 + 学生画像完善
- **v0.3**: 学习分析 + Docker 部署
- **v0.4**: MCP 协议 + 云部署 + 可观测性

## License

MIT
