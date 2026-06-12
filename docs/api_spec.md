# TutorMind API 规格说明书 (API Spec)

## 1. 概述

TutorMind API 基于 RESTful 设计，使用 JSON 格式进行数据交换。

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **认证**: 当前版本使用学生 ID 进行身份识别（后续版本可集成 JWT）

## 2. API 端点

### 2.1 健康检查

```
GET /health
```

**响应**:
```json
{
  "status": "ok",
  "app": "TutorMind",
  "version": "0.1.0",
  "model": "qwen-plus"
}
```

---

### 2.2 对话接口

#### 发送消息

```
POST /api/chat/
```

**请求体**:
```json
{
  "student_id": "student_001",
  "session_id": "uuid-xxxx-xxxx",
  "message": "能教我什么是牛顿第二定律吗？"
}
```

**响应**:
```json
{
  "student_id": "student_001",
  "session_id": "uuid-xxxx-xxxx",
  "reply": "你好！在开始之前，我想先了解...",
  "agent_name": "info_collector",
  "stage": "collect_info",
  "is_guided": false,
  "metadata": {
    "kb_hit": false,
    "is_weak_foundation": false
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| student_id | string | 学生唯一标识 |
| session_id | string | 会话唯一标识 |
| message | string | 学生输入的问题 |
| reply | string | 系统回复内容 |
| agent_name | string | 处理该请求的 Agent 名称 |
| stage | string | 当前流程阶段 |
| is_guided | bool | 是否使用了苏格拉底引导 |
| metadata | object | 附加元数据 |

**agent_name 取值**:
- `info_collector` — 信息收集阶段
- `socratic_tutor` — 苏格拉底引导阶段
- `search_agent` — 实时搜索阶段

**stage 取值**:
- `check_student_info` — 检查学生信息
- `collect_info` — 收集学生信息
- `search_knowledge_base` — 检索知识库
- `socratic_teach` — 苏格拉底教学
- `tavily_search` — Tavily 搜索
- `generate_answer` — 生成答案

#### 创建会话

```
POST /api/chat/create_session/{student_id}
```

**响应**:
```json
{
  "student_id": "student_001",
  "session_id": "uuid-xxxx-xxxx"
}
```

---

### 2.3 学生信息接口

#### 获取学生信息

```
GET /api/students/{student_id}
```

**响应**:
```json
{
  "student_id": "student_001",
  "name": "小明",
  "age": 15,
  "education": "初中三年级",
  "is_weak_foundation": true,
  "learning_goals": "准备中考数学"
}
```

#### 更新学生信息

```
PUT /api/students/{student_id}
```

**请求体**:
```json
{
  "education": "高中一年级",
  "is_weak_foundation": false
}
```

#### 创建学生

```
POST /api/students/
```

**请求体**:
```json
{
  "student_id": "student_002",
  "name": "小红",
  "age": 20,
  "education": "大学二年级",
  "is_weak_foundation": false
}
```

#### 获取学生问答历史

```
GET /api/students/{student_id}/history?limit=20
```

**响应**:
```json
{
  "student_id": "student_001",
  "history": [
    {
      "question": "什么是牛顿第二定律？",
      "answer": "牛顿第二定律指出...",
      "source": "tavily_search",
      "similarity_score": null,
      "topic_tags": null,
      "is_guided": false,
      "created_at": "2026-06-11T10:15:00"
    }
  ]
}
```

---

### 2.4 学习分析接口

#### 获取学习报告

```
GET /api/analytics/{student_id}
```

**响应**:
```json
{
  "student_id": "student_001",
  "total_questions": 25,
  "guided_sessions": 12,
  "search_sessions": 13,
  "common_topics": ["数学", "物理"],
  "weak_foundation": true,
  "created_at": "2026-06-11T15:00:00"
}
```

#### 获取学习摘要

```
GET /api/analytics/{student_id}/summary
```

**响应**:
```json
{
  "student_id": "student_001",
  "total_messages": 156,
  "recent_messages": 23,
  "total_sessions": 5
}
```

---

## 3. 错误码定义

| HTTP 状态码 | 错误码 | 说明 |
|-----------|--------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 404 | NOT_FOUND | 学生不存在 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 500 | LLM_ERROR | LLM 调用失败 |
| 500 | SEARCH_ERROR | 搜索服务失败 |
| 500 | DB_ERROR | 数据库操作失败 |

**错误响应格式**:
```json
{
  "detail": "Student not found",
  "error_code": "NOT_FOUND"
}
```

---

## 4. 数据模型

### StudentProfile
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学生唯一标识 |
| name | string | 否 | 姓名 |
| age | integer | 否 | 年龄 |
| education | string | 否 | 学历/年级 |
| is_weak_foundation | bool | 否 | 是否基础薄弱 |
| learning_goals | string | 否 | 学习目标 |

### ChatRequest
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学生ID |
| session_id | string | 是 | 会话ID |
| message | string | 是 | 消息内容 |

### ChatResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| student_id | string | 学生ID |
| session_id | string | 会话ID |
| reply | string | 回复内容 |
| agent_name | string | 处理Agent |
| stage | string | 流程阶段 |
| is_guided | bool | 是否引导 |
| metadata | object | 元数据 |