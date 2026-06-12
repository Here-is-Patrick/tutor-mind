# TutorMind — 一对一学习辅导 Agent

基于 LangGraph + CrewAI 多智能体协作的智能学习辅导系统。

## 核心功能

- **学生信息收集**: 自动检测缺失信息并礼貌追问
- **知识库优先检索**: 向量检索相似历史问题，复用教学路径
- **苏格拉底式引导**: 递进式提问引导学生自行推导答案
- **实时搜索兜底**: 知识库未命中时调用 Tavily Search API
- **自适应教学风格**: 根据学生基础水平调整回答难度和语言风格
- **多智能体协作**: LangGraph 状态机编排 + CrewAI 多 Agent 协作

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Python 3.11+ |
| 状态编排 | LangGraph (StateGraph) |
| 多Agent协作 | CrewAI |
| LLM | 阿里云百炼 DashScope (千问系列) |
| 向量数据库 | ChromaDB |
| 结构化存储 | SQLite |
| 实时搜索 | Tavily Search API |
| 前端 | React 18 + TypeScript + Tailwind CSS |
| 部署 | Docker + Docker Compose |

## 项目结构

```
tutor-mind/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理
│   │   ├── agents/                 # Agent 实现
│   │   │   ├── orchestrator.py
│   │   │   ├── info_collector.py
│   │   │   ├── knowledge_retriever.py
│   │   │   ├── socratic_tutor.py
│   │   │   └── search_agent.py
│   │   ├── tools/                  # 工具函数
│   │   ├── graph/                  # LangGraph 状态机
│   │   ├── models/                 # 数据模型
│   │   ├── rag/                    # RAG 实现
│   │   ├── memory/                # 记忆机制
│   │   ├── crew/                  # CrewAI 编排
│   │   └── api/                    # API 路由
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/                        # React 前端
├── docs/                           # 文档
├── docker-compose.yml
└── README.md
```

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- 阿里云百炼 DashScope API Key
- Tavily Search API Key

### 1. 克隆项目

```bash
git clone <repo-url>
cd tutor-mind
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

```env
DASHSCOPE_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
LLM_MODEL=qwen-plus
```

### 3. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动后端

```bash
cd backend
python -m app.main
# 或
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 使用对话界面。

### 6. Docker 部署（可选）

```bash
# 配置好 .env 文件后
docker-compose up -d
```

前端访问 http://localhost:3000，后端 API 在 http://localhost:8000。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/chat/` | 发送消息 |
| POST | `/api/chat/create_session/{id}` | 创建会话 |
| GET | `/api/students/{id}` | 获取学生信息 |
| PUT | `/api/students/{id}` | 更新学生信息 |
| POST | `/api/students/` | 创建学生 |
| GET | `/api/students/{id}/history` | 获取问答历史 |
| GET | `/api/analytics/{id}` | 获取学习报告 |
| GET | `/api/analytics/{id}/summary` | 获取学习摘要 |

## 系统架构

```
学生输入 → check_student_info
              │
    ┌─────────┴─────────┐
    ▼                   ▼
信息完整            信息不完整 → collect_info
    │
    ▼
search_knowledge_base (ChromaDB)
    │
┌───┴───┐
▼       ▼
命中    未命中
│       │
Socratic  Tavily Search
Teach     │
│       generate_answer
└───┬───┘
    ▼
 return final_reply
```

## 运行测试

```bash
cd backend
pytest tests/ -v
```

## 文档

- [产品规格说明书](docs/product_spec.md)
- [架构规格说明书](docs/architecture_spec.md)
- [API 规格说明书](docs/api_spec.md)

## 开发路线图

- **v0.1 (MVP)**: 核心 Agent 功能 + 前端对话界面
- **v0.2**: 苏格拉底引导优化 + 学生画像完善
- **v0.3**: 学习分析 + Docker 部署
- **v0.4**: MCP 协议 + 云部署 + 可观测性

## License

MIT