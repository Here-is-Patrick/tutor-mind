# TutorMind — 一对一智能学习辅导系统

## 项目概述

TutorMind 是一个基于 **LangGraph + 多智能体（Multi-Agent）协作** 的智能学习辅导系统。系统通过多个专门化的 AI Agent 协同工作，为学生提供个性化的学习辅导体验，包括学生信息收集、知识库检索、苏格拉底式引导教学、实时搜索兜底等功能。

---

## 核心功能

| 功能 | 说明 |
|------|------|
| **学生信息收集** | 自动检测缺失信息并礼貌追问，建立学生画像 |
| **知识库优先检索** | 向量检索相似历史问题，复用教学路径 |
| **苏格拉底式引导** | 递进式提问引导学生自行推导答案 |
| **实时搜索兜底** | 知识库未命中时调用 Tavily Search API |
| **自适应教学风格** | 根据学生基础水平调整回答难度和语言风格 |
| **多智能体协作** | LangGraph 状态机编排多 Agent 协作 |
| **流式响应** | SSE 实时流式输出，提升交互体验 |
| **会话管理** | 支持多会话、删除会话、删除单条消息 |
| **用户隔离** | 不同学生的知识库和会话历史完全隔离 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Python 3.11+ |
| 状态编排 | LangGraph (StateGraph) |
| LLM | 阿里云百炼 DashScope (通义千问系列) |
| Embedding | DashScope text-embedding-v2 |
| 向量数据库 | ChromaDB |
| 结构化存储 | SQLite |
| 实时搜索 | Tavily Search API |
| 前端 | React 18 + TypeScript + Tailwind CSS |
| 部署 | Docker + Docker Compose |

---

## 多智能体架构

TutorMind 采用 **多智能体协作架构**，每个 Agent 负责特定的任务，通过 LangGraph 状态机进行编排调度。

### Agent 列表

#### 1. Orchestrator Agent（编排器）
- **文件**: `backend/app/agents/orchestrator.py`
- **职责**:
  - 协调整个学习辅导流程
  - 提供统一的 LLM 调用能力（封装 DashScope API）
  - 管理对话上下文（短期记忆 + 长期记忆）
  - 保存对话回合到记忆系统
- **核心方法**:
  - `call_llm()` — 调用大语言模型生成回复
  - `save_conversation_turn()` — 保存对话到短期和长期记忆
  - `get_conversation_context()` — 获取会话上下文

#### 2. InfoCollector Agent（信息收集器）
- **文件**: `backend/app/agents/info_collector.py`
- **职责**:
  - 检查学生信息是否完整（姓名、年龄、学历、基础水平）
  - 从学生自然语言输入中提取结构化信息
  - 礼貌地追问缺失信息
- **核心方法**:
  - `check()` — 检查学生画像完整性
  - `collect()` — 收集并解析学生输入中的信息
  - `_extract_info()` — 使用 LLM 提取信息
  - `_extract_regex()` — 正则表达式兜底提取

#### 3. KnowledgeRetriever Agent（知识检索器）
- **文件**: `backend/app/agents/knowledge_retriever.py`
- **职责**:
  - 从向量知识库（ChromaDB）中检索相似历史问答
  - 判断匹配质量是否足够触发苏格拉底教学
  - 支持按学生 ID 过滤，确保数据隔离
- **核心方法**:
  - `search()` — 检索相似问题
  - `get_cached_answer()` — 获取精确匹配的缓存答案

#### 4. SocraticTutor Agent（苏格拉底导师）
- **文件**: `backend/app/agents/socratic_tutor.py`
- **职责**:
  - 采用苏格拉底教学法，不直接给出答案
  - 基于相似问题的历史解答，设计递进式引导提问
  - 根据学生基础水平调整提问难度
  - 将交互保存到知识库供未来复用
- **核心方法**:
  - `teach()` — 生成苏格拉底式引导问题

#### 5. Search Agent（搜索代理）
- **文件**: `backend/app/agents/search_agent.py`
- **职责**:
  - 调用 Tavily Search API 进行实时网络搜索
  - 基于搜索结果生成结构化答案
  - 根据学生基础水平自适应调整语言风格
  - 将问答保存到知识库供未来复用
- **核心方法**:
  - `search()` — 执行 Tavily 搜索
  - `generate_answer()` — 基于搜索结果生成答案

---

## 工作流程（Pipeline）

系统通过 **LangGraph StateGraph** 编排以下工作流：

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
                    │               │
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

### 流程说明

1. **check_student_info**: 检查学生画像是否完整，若不完整则进入信息收集流程
2. **collect_info**: 收集学生信息，支持从自然语言中自动提取姓名、年龄、学历、基础水平
3. **search_knowledge_base**: 将学生问题向量化，在 ChromaDB 中检索相似历史问答
4. **socratic_teach**: 若知识库命中，基于历史解答采用苏格拉底式引导教学
5. **tavily_search**: 若知识库未命中，调用 Tavily API 进行实时网络搜索
6. **generate_answer**: 基于搜索结果生成结构化答案，并自适应学生基础水平
7. **save_conversation_turn**: 将本轮对话保存到短期记忆和长期记忆
8. **rebuild_short_term_memory**: 从数据库重建会话的短期记忆，确保上下文连贯

---

## 记忆系统

系统采用 **双层记忆架构**：

### 短期记忆（Short-Term Memory）
- **文件**: `backend/app/memory/short_term.py`
- **特点**:
  - 内存中的滑动窗口缓冲区
  - 按会话（session）隔离
  - 默认保存最近 20 条消息
  - 用于 LLM 上下文构建

### 长期记忆（Long-Term Memory）
- **文件**: `backend/app/memory/long_term.py`
- **特点**:
  - 持久化存储在 SQLite 数据库
  - 保存所有会话消息和 QA 记录
  - 支持会话标题自动生成（取第一条学生消息）
  - 服务器重启后可通过 DB 恢复上下文

---

## RAG（检索增强生成）

系统内置完整的 RAG  pipeline：

### 组件

| 组件 | 文件 | 说明 |
|------|------|------|
| Embedding 模型 | `backend/app/rag/embeddings.py` | DashScope text-embedding-v2 |
| 向量存储 | `backend/app/rag/vector_store.py` | ChromaDB 持久化存储 |
| 检索器 | `backend/app/rag/retriever.py` | 封装嵌入+检索+过滤逻辑 |

### 数据流

1. 学生提问 → Embedding 模型生成向量
2. 在 ChromaDB 中搜索相似 QA 记录
3. 按相似度阈值过滤（默认 0.7）
4. 按学生 ID 过滤，确保不同学生的数据隔离
5. 返回最相似的问答作为教学参考

---

## 前端界面

前端采用 React + TypeScript + Tailwind CSS 构建，主要组件：

### ChatPanel（聊天面板）
- 实时流式消息展示
- Markdown 渲染支持
- 消息删除功能
- Agent 名称标签显示（如"苏格拉底导师"、"知识搜索"）
- 自动滚动到底部

### Sidebar（侧边栏）
- 学生信息展示（姓名、年龄、学历、基础水平）
- 学习概览统计（当前会话消息数、总会话数）
- 历史会话列表（支持标题显示、删除）
- 用户切换/新建功能
- localStorage 持久化上次登录用户

---

## 项目结构

```
tutor-mind/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理
│   │   ├── agents/                 # Agent 实现
│   │   │   ├── orchestrator.py     # 编排器 + LLM 调用
│   │   │   ├── info_collector.py   # 信息收集器
│   │   │   ├── knowledge_retriever.py  # 知识检索器
│   │   │   ├── socratic_tutor.py   # 苏格拉底导师
│   │   │   └── search_agent.py     # 搜索代理
│   │   ├── tools/                  # 工具函数
│   │   │   ├── tavily_tool.py      # Tavily API 封装
│   │   │   ├── kb_search.py        # 知识库搜索工具
│   │   │   ├── foundation_check.py # 基础水平检测
│   │   │   └── student_profile.py  # 学生画像管理
│   │   ├── graph/                  # LangGraph 状态机
│   │   │   ├── state.py            # TutorState 状态定义
│   │   │   └── workflow.py         # 工作流编排
│   │   ├── models/                 # 数据模型
│   │   │   ├── schemas.py          # Pydantic 模型
│   │   │   └── database.py         # SQLite 数据库操作
│   │   ├── rag/                    # RAG 实现
│   │   │   ├── embeddings.py       # Embedding 生成
│   │   │   ├── vector_store.py     # ChromaDB 向量存储
│   │   │   └── retriever.py        # 检索器
│   │   ├── memory/                 # 记忆机制
│   │   │   ├── short_term.py       # 短期记忆（内存滑动窗口）
│   │   │   └── long_term.py        # 长期记忆（SQLite 持久化）
│   │   └── api/                    # API 路由
│   │       └── chat.py             # 聊天 API（流式/非流式）
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.tsx                 # 主应用组件
│       ├── components/
│       │   ├── ChatPanel.tsx       # 聊天面板
│       │   └── Sidebar.tsx         # 侧边栏
│       ├── services/
│       │   └── api.ts              # API 调用封装
│       └── types.ts                # TypeScript 类型定义
├── docker-compose.yml
└── README.md
```

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/` | 发送消息（非流式） |
| POST | `/api/chat/stream` | 发送消息（SSE 流式） |
| POST | `/api/chat/create_session/{student_id}` | 创建新会话 |
| GET | `/api/chat/history/{student_id}/{session_id}` | 获取会话历史 |
| GET | `/api/chat/sessions/{student_id}` | 获取学生所有会话 |
| DELETE | `/api/chat/session/{student_id}/{session_id}` | 删除会话 |
| DELETE | `/api/chat/message/{student_id}/{session_id}/{message_id}` | 删除单条消息 |
| GET | `/api/students/{id}` | 获取学生信息 |
| PUT | `/api/students/{id}` | 更新学生信息 |
| POST | `/api/students/` | 创建学生 |
| GET | `/api/analytics/{id}` | 获取学习报告 |
| GET | `/api/analytics/{id}/summary` | 获取学习摘要 |

---

## 特色设计

### 1. 自适应教学
系统根据学生的基础水平（`is_weak_foundation`）动态调整：
- **基础薄弱**: 使用更简单直白的语言，更多解释和例子
- **有一定基础**: 使用更专业的术语，更深入的推导

### 2. 知识复用
每次问答都会保存到向量知识库，后续相似问题可以直接复用历史教学路径，减少 LLM 调用成本并提高一致性。

### 3. 数据隔离
- 知识库检索按 `student_id` 过滤，确保学生 A 的问题不会被学生 B 看到
- 会话历史按 session 隔离，每个会话只能看到自己的消息

### 4. 记忆持久化
- 短期记忆在内存中，重启后丢失
- 长期记忆在 SQLite 中，重启后可通过 `get_conversation_context()` 自动恢复

---

## 开发路线图

- **v0.1 (MVP)**: 核心 Agent 功能 + 前端对话界面
- **v0.2**: 苏格拉底引导优化 + 学生画像完善
- **v0.3**: 学习分析 + Docker 部署
- **v0.4**: MCP 协议 + 云部署 + 可观测性

---

## License

MIT
