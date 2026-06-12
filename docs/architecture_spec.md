# TutorMind 架构规格说明书 (Architecture Spec)

## 1. 系统架构概览 (C4 Model)

### 1.1 Context Diagram (系统上下文)

```
┌─────────────────────────────────────────────────────────┐
│                      学生用户                            │
└──────────────┬──────────────────────────────────────────┘
               │ HTTP/REST
               ▼
┌─────────────────────────────────────────────────────────┐
│                    TutorMind System                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │              React Frontend (Port 3000)           │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │ REST API                           │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │           FastAPI Backend (Port 8000)             │   │
│  │  ┌─────────────────────────────────────────┐     │   │
│  │  │  LangGraph StateGraph (Orchestrator)     │     │   │
│  │  │  CrewAI Multi-Agent (Alt Orchestrator)   │     │   │
│  │  └─────────────────────────────────────────┘     │   │
│  └──┬───────────┬──────────┬───────────────┬────────┘   │
│     │           │          │               │             │
│     ▼           ▼          ▼               ▼             │
│ ┌───────┐ ┌────────┐ ┌─────────┐ ┌──────────────┐      │
│ │SQLite │ │ChromaDB│ │DashScope│ │Tavily Search │      │
│ └───────┘ └────────┘ └─────────┘ └──────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Container Diagram (容器视图)

```
┌──────────────────────────────────────────────────────────┐
│                    TutorMind System                       │
│                                                           │
│  ┌──────────────────┐   ┌─────────────────────────────┐  │
│  │  Frontend         │   │  Backend (FastAPI)           │  │
│  │  React + TS       │──▶│  Port 8000                   │  │
│  │  Tailwind CSS     │   │                              │  │
│  │  Port 80/3000     │   │  ┌────────────────────────┐  │  │
│  └──────────────────┘   │  │ LangGraph Workflow      │  │  │
│                          │  │  ├─ check_student_info  │  │  │
│                          │  │  ├─ collect_info        │  │  │
│                          │  │  ├─ search_knowledge    │  │  │
│                          │  │  ├─ socratic_teach      │  │  │
│                          │  │  ├─ tavily_search       │  │  │
│                          │  │  └─ generate_answer     │  │  │
│                          │  └────────────────────────┘  │  │
│                          │                              │  │
│                          │  ┌────────────────────────┐  │  │
│                          │  │ CrewAI Orchestration    │  │  │
│                          │  │  ├─ InfoCollector       │  │  │
│                          │  │  ├─ KnowledgeRetriever  │  │  │
│                          │  │  ├─ SocraticTutor       │  │  │
│                          │  │  └─ SearchAgent         │  │  │
│                          │  └────────────────────────┘  │  │
│                          └──────────────────────────────┘  │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ SQLite   │  │ ChromaDB │  │DashScope │  │ Tavily  │  │
│  │(持久化)  │  │(向量库)  │  │(LLM/Emb) │  │(搜索)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 2. Agent 交互流程

```
学生输入 → check_student_info
              │
    ┌─────────┴─────────┐
    ▼                   ▼
信息完整            信息不完整
    │                   │
    │              collect_info (追问)
    │                   │
    │              ┌────┴────┐
    │              ▼         ▼
    │         信息完整   信息仍不完整
    │              │         │
    │              │    END (返回追问)
    └──────┬───────┘
           ▼
   search_knowledge_base (ChromaDB向量检索)
           │
    ┌──────┴──────┐
    ▼              ▼
 kb_hit=true   kb_hit=false
    │              │
socratic_teach  tavily_search
    │              │
    │         generate_answer
    │              │
    └──────┬───────┘
           ▼
        END (返回final_reply)
```

## 3. 数据流图

```
┌─────────────┐     ┌───────────────┐     ┌─────────────┐
│  Student     │────▶│  FastAPI      │────▶│  LangGraph  │
│  Input       │     │  /api/chat    │     │  Workflow   │
└─────────────┘     └───────────────┘     └──────┬──────┘
                                                  │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    ▼                              ▼                              ▼
            ┌──────────────┐             ┌────────────────┐            ┌─────────────────┐
            │ InfoCollector │             │KnowledgeRetriev│            │  SearchAgent     │
            │               │             │                │            │                 │
            │ get_profile() │             │  embed_query() │            │ tavily_search() │
            │ save_profile()│             │  search_top3() │            │ format_answer() │
            └──────┬───────┘             └───────┬────────┘            └────────┬────────┘
                   │                             │                              │
                   ▼                             ▼                              ▼
            ┌──────────┐                 ┌───────────┐                 ┌──────────────┐
            │  SQLite  │                 │ ChromaDB  │                 │  Tavily API  │
            │ students │                 │qa_embed   │                 │  (External)  │
            │ messages │                 └───────────┘                 └──────────────┘
            │ qa_records│
            │ sessions │
            └──────────┘

                    ┌─────────────────────────────────────────────┐
                    │           Memory Layer                      │
                    │  ┌─────────────────┐ ┌──────────────────┐   │
                    │  │ ShortTermMemory │ │ LongTermMemory   │   │
                    │  │ (sliding window)│ │ (SQLite persist) │   │
                    │  └─────────────────┘ └──────────────────┘   │
                    └─────────────────────────────────────────────┘
```

## 4. 学生画像设计

```json
{
  "student_id": "student_001",
  "name": "小明",
  "age": 15,
  "education": "初中三年级",
  "is_weak_foundation": true,
  "learning_goals": "准备中考数学",
  "created_at": "2026-06-11T10:00:00",
  "updated_at": "2026-06-11T14:30:00"
}
```

## 5. 技术选型理由

| 技术 | 选型理由 |
|------|---------|
| **Python 3.11+** | 主流 AI/ML 生态，LangChain/LangGraph/CrewAI 原生支持 |
| **LangGraph** | 状态机编排，支持条件路由和检查点，适合多步骤推理 |
| **LangChain** | 成熟的 LLM 框架，提供 Embedding/RAG/Tools 抽象 |
| **CrewAI** | 多智能体协作编排，Agent 角色定义清晰，适合本场景 |
| **FastAPI** | 高性能异步 Python Web 框架，自动 OpenAPI 文档 |
| **ChromaDB** | 轻量嵌入式向量数据库，无需额外部署，支持持久化 |
| **SQLite** | 零配置结构化存储，适合学生画像和对话记录 |
| **DashScope** | 阿里云百炼 API，千问系列中文能力强，价格合理 |
| **Tavily** | 专为 AI Agent 设计的搜索 API，返回结构化结果 |
| **React + Tailwind** | 成熟的现代前端框架，快速构建对话界面 |