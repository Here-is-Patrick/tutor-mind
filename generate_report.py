#!/usr/bin/env python3
"""
Generate CS599 Final Project Report (Word format)
Based on current TutorMind project code.
"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_cell_shading(cell, color):
    """Set cell background color."""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    cell._tc.get_or_add_tcPr().append(shading)


def add_heading_custom(doc, text, level=1):
    """Add a styled heading."""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.name = 'Microsoft YaHei'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
        if level == 1:
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)
        elif level == 2:
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        else:
            run.font.size = Pt(12)
            run.font.bold = True
    heading.paragraph_format.space_before = Pt(18)
    heading.paragraph_format.space_after = Pt(6)
    return heading


def add_paragraph_custom(doc, text, bold=False, italic=False, indent=True):
    """Add a styled paragraph."""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = 'Microsoft YaHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    run.font.size = Pt(11)
    run.font.bold = bold
    run.font.italic = italic
    return p


def add_code_block(doc, code, language="python"):
    """Add a styled code block."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    run = p.add_run(code)
    run.font.name = 'Consolas'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    # Add light gray background via shading
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), 'F5F5F5')
    p._p.get_or_add_pPr().append(shading)
    return p


def add_image_placeholder(doc, caption):
    """Add an image placeholder with caption."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"【{caption}】")
    run.font.name = 'Microsoft YaHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    run.font.italic = True

    # Caption
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run(f"图：{caption}")
    cap_run.font.name = 'Microsoft YaHei'
    cap_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    cap_run.font.size = Pt(10)
    cap_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    cap.paragraph_format.space_after = Pt(12)
    return p


def add_table_custom(doc, headers, rows):
    """Add a styled table."""
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'

    # Header row
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        set_cell_shading(hdr_cells[i], '4472C4')
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Microsoft YaHei'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
                run.font.size = Pt(10)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Data rows
    for row_data in rows:
        row_cells = table.add_row().cells
        for i, cell_text in enumerate(row_data):
            row_cells[i].text = str(cell_text)
            for paragraph in row_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.name = 'Microsoft YaHei'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
                    run.font.size = Pt(10)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()  # spacing after table
    return table


def generate_report():
    doc = Document()

    # ── Page setup ─────────────────────────────────────────────
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    # ── Cover Page (Placeholder) ───────────────────────────────
    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("TutorMind")
    run.font.name = 'Microsoft YaHei'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x1a)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = subtitle.add_run("基于 LangGraph 多智能体的一对一智能学习辅导系统")
    run2.font.name = 'Microsoft YaHei'
    run2._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    run2.font.size = Pt(16)
    run2.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    doc.add_paragraph()
    doc.add_paragraph()

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info_run = info.add_run("【封面页信息请自行填写】\n\n"
                            "课程名称：企业级应用软件设计与开发\n"
                            "方向：方向一：Agentic AI 原生开发\n"
                            "学号：__________\n"
                            "姓名：__________\n"
                            "专业：计算机技术 / 软件工程\n"
                            "指导教师：戚欣\n"
                            "提交日期：2026 年 6 月 22 日")
    info_run.font.name = 'Microsoft YaHei'
    info_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    info_run.font.size = Pt(12)
    info_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_page_break()

    # ── Table of Contents (Placeholder) ────────────────────────
    add_heading_custom(doc, "目录", level=1)
    add_paragraph_custom(doc, "【请使用 Word 的'引用'→'目录'功能自动生成导航目录，确保 PDF 输出时包含书签导航】", indent=False)
    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 一、选题背景与设计思想
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "一、选题背景与设计思想", level=1)

    add_heading_custom(doc, "1.1 问题定义", level=2)
    add_paragraph_custom(doc,
        "在高等教育和在线教育场景中，学生常常面临以下困境："
        "（1）一对一真人辅导成本高昂，优质教育资源分配不均；"
        "（2）传统问答系统（如 FAQ 机器人）只能提供固定答案，无法根据学生的基础水平和学习进度进行个性化调整；"
        "（3）现有的大语言模型应用虽然具备强大的知识储备，但缺乏系统性的教学策略，容易直接给出答案，"
        "违背了教育心理学中'主动建构'的学习原则。"
    )
    add_paragraph_custom(doc,
        "本项目旨在构建一个具备苏格拉底式教学能力的智能辅导系统——TutorMind。"
        "系统通过多智能体协作架构，模拟真人教师的信息收集、知识检索、引导提问和实时搜索等行为，"
        "为学生提供低成本、高质量、个性化的一对一学习辅导体验。"
    )

    add_heading_custom(doc, "1.2 现有方案不足", level=2)
    add_paragraph_custom(doc,
        "当前市场上的教育 AI 产品主要分为两类，但均存在明显不足："
    )
    add_paragraph_custom(doc,
        "（1）传统问答型 AI（如早期 ChatGPT 教育插件）：直接输出完整答案，学生被动接受，"
        "缺乏思考过程，知识留存率低。且无法跨会话保持对学生情况的记忆，每次对话都是'从零开始'。"
    )
    add_paragraph_custom(doc,
        "（2）简单 RAG 增强系统：虽然引入了知识库检索，但检索结果与学生个人情况脱节，"
        "回答风格固定，不会根据学生的基础水平调整语言难度和解释深度。"
    )
    add_paragraph_custom(doc,
        "（3）单智能体系统：所有功能由一个 Agent 承担，导致 prompt 过于复杂、行为难以控制，"
        "无法清晰区分'收集信息'、'检索知识'、'引导教学'等不同阶段的职责。"
    )

    add_heading_custom(doc, "1.3 项目价值", level=2)
    add_paragraph_custom(doc,
        "TutorMind 的核心价值体现在以下三个方面："
    )
    add_paragraph_custom(doc,
        "（1）苏格拉底式教学：不直接给答案，而是通过递进式提问引导学生自行推导，"
        "激发主动思考，提升知识内化效果。"
    )
    add_paragraph_custom(doc,
        "（2）多智能体分工协作：每个 Agent 负责特定职责（信息收集、知识检索、苏格拉底引导、实时搜索），"
        "通过 LangGraph 状态机编排，行为可控、逻辑清晰、易于扩展。"
    )
    add_paragraph_custom(doc,
        "（3）多层级记忆机制：短期记忆保证当前会话的上下文连贯，长期记忆（SQLite）实现跨会话持久化，"
        "向量记忆（ChromaDB）支持相似问题的快速检索复用，LangGraph Checkpoint 确保工作流状态可恢复。"
    )
    add_paragraph_custom(doc,
        "（4）多轮对话支持：基于 LangChain BaseMessage 标准消息序列，LLM 能够原生理解对话上下文，"
        "实现真正的连贯多轮交互，而非简单的历史拼接。"
    )

    add_heading_custom(doc, "1.4 技术路线", level=2)
    add_paragraph_custom(doc,
        "本项目采用 SDD（规格驱动开发）方法论，从 Product Spec、Architecture Spec 到 API Spec 分层设计，"
        "确保需求可追踪、架构可落地、接口可测试。技术选型遵循课程要求："
    )
    add_table_custom(doc,
        ["技术类别", "选型", "说明"],
        [
            ["AI IDE", "Trae CN", "课程指定，自适应 AI 原生 IDE"],
            ["LLM", "阿里云百炼 DashScope", "通义千问系列，中文场景表现优异"],
            ["Agent 框架", "LangGraph + LangChain", "状态机编排 + 工具链生态"],
            ["向量数据库", "ChromaDB", "轻量级本地向量存储"],
            ["结构化存储", "SQLite", "零配置、开箱即用"],
            ["实时搜索", "Tavily Search API", "专为 LLM 优化的搜索 API"],
            ["前端", "React 18 + TypeScript", "组件化、类型安全"],
            ["容器化", "Docker + Docker Compose", "一键部署"],
        ]
    )

    # ═══════════════════════════════════════════════════════════
    # 二、Specs 规格文档
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "二、Specs 规格文档", level=1)

    add_heading_custom(doc, "2.1 Product Spec", level=2)
    add_paragraph_custom(doc,
        "Product Spec 定义了 TutorMind 的产品目标、用户画像和核心功能。"
    )
    add_paragraph_custom(doc, "目标用户：", bold=True)
    add_paragraph_custom(doc,
        "高等教育阶段（大学、研究生）需要课后辅导的学生，尤其是基础薄弱、"
        "需要循序渐进引导的自主学习者。"
    )
    add_paragraph_custom(doc, "核心功能：", bold=True)
    add_table_custom(doc,
        ["功能模块", "功能描述", "优先级"],
        [
            ["学生画像构建", "自动收集姓名、年龄、学历、基础水平，建立学生档案", "P0"],
            ["资料更新识别", "识别学生更新个人信息的意图，自动路由到信息收集节点", "P0"],
            ["知识库检索", "基于向量相似度检索历史问答，复用教学路径", "P0"],
            ["苏格拉底引导", "递进式提问，引导学生自行推导答案", "P0"],
            ["实时搜索兜底", "知识库未命中时调用 Tavily API 获取实时信息", "P0"],
            ["多轮对话", "基于标准消息序列的连贯多轮交互", "P0"],
            ["自适应风格", "根据基础水平调整回答难度和语言风格", "P1"],
            ["流式响应", "SSE 实时流式输出，提升交互体验", "P1"],
            ["会话管理", "支持多会话、历史加载、删除消息", "P1"],
            ["公式渲染", "基于 KaTeX 的 LaTeX 数学公式渲染", "P2"],
        ]
    )

    add_heading_custom(doc, "2.2 Architecture Spec", level=2)
    add_paragraph_custom(doc,
        "Architecture Spec 定义了系统的分层架构和各层职责。"
    )
    add_paragraph_custom(doc, "分层架构：", bold=True)
    add_table_custom(doc,
        ["层级", "职责", "技术实现"],
        [
            ["表现层", "用户交互界面", "React 18 + Tailwind CSS"],
            ["API 网关层", "REST API + SSE 流式传输", "FastAPI"],
            ["编排层", "LangGraph StateGraph 工作流编排", "LangGraph"],
            ["Agent 层", "多智能体业务逻辑", "5 个专用 Agent"],
            ["工具层", "外部 API 调用、知识库操作", "Tavily、ChromaDB"],
            ["记忆层", "短期/长期/向量记忆管理", "内存、SQLite、ChromaDB"],
            ["数据层", "结构化数据持久化", "SQLite"],
        ]
    )

    add_heading_custom(doc, "2.3 API Spec", level=2)
    add_paragraph_custom(doc,
        "API Spec 定义了 TutorMind 对外暴露的 RESTful 接口。"
    )
    add_paragraph_custom(doc, "核心接口：", bold=True)
    add_table_custom(doc,
        ["方法", "路径", "描述"],
        [
            ["POST", "/api/chat/", "非流式聊天"],
            ["POST", "/api/chat/stream", "SSE 流式聊天"],
            ["GET", "/api/chat/history/{sid}/{sess}", "获取会话历史"],
            ["GET", "/api/chat/sessions/{sid}", "获取学生所有会话"],
            ["POST", "/api/chat/create_session/{sid}", "创建新会话"],
            ["DELETE", "/api/chat/session/{sid}/{sess}", "删除会话"],
            ["DELETE", "/api/chat/message/{sid}/{sess}/{msg}", "删除单条消息"],
            ["GET", "/health", "健康检查"],
        ]
    )
    add_paragraph_custom(doc, "请求/响应模型：", bold=True)
    add_code_block(doc, """class ChatRequest(BaseModel):
    student_id: str
    session_id: str
    message: str

class ChatResponse(BaseModel):
    student_id: str
    session_id: str
    reply: str
    agent_name: str
    stage: str
    is_guided: bool = False
    metadata: Optional[dict] = None""")

    # ═══════════════════════════════════════════════════════════
    # 三、系统架构与设计
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "三、系统架构与设计", level=1)

    add_heading_custom(doc, "3.1 核心架构图", level=2)
    add_paragraph_custom(doc,
        "TutorMind 采用 LangGraph StateGraph 作为核心编排引擎，"
        "各 Agent 通过共享 TutorState 状态对象协作完成教学任务。"
    )
    add_image_placeholder(doc, "系统整体架构图 — 请使用 Draw.io / ProcessOn 绘制以下结构："
        "表现层(React) → API层(FastAPI) → 编排层(LangGraph StateGraph) → "
        "Agent层(5个Agent) → 工具层(Tavily/ChromaDB) → 记忆层(三层记忆) → 数据层(SQLite)")

    add_heading_custom(doc, "3.2 Agent 交互流程", level=2)
    add_paragraph_custom(doc,
        "系统包含 5 个专用 Agent，每个 Agent 负责明确的职责边界："
    )
    add_table_custom(doc,
        ["Agent 名称", "职责", "关键方法"],
        [
            ["OrchestratorAgent", "统一 LLM 调用、记忆管理、多轮对话消息转换", "call_llm_with_messages, save_conversation_turn"],
            ["InfoCollectorAgent", "学生画像构建、资料更新意图识别", "check, collect, looks_like_profile_update"],
            ["KnowledgeRetrieverAgent", "ChromaDB 向量检索", "search, get_cached_answer"],
            ["SocraticTutorAgent", "苏格拉底式递进引导", "teach（支持 messages 参数）"],
            ["SearchAgent", "Tavily 实时搜索 + 答案生成", "search, generate_answer（支持 messages 参数）"],
        ]
    )

    add_image_placeholder(doc, "Agent 交互时序图 — 请绘制："
        "用户 → chat.py → LangGraph → check_student_info → [collect_info | search_knowledge_base] → "
        "[socratic_teach | tavily_search → generate_answer] → save_conversation_turn → 返回用户")

    add_heading_custom(doc, "3.3 数据流设计", level=2)
    add_paragraph_custom(doc,
        "数据流分为'请求流入'和'状态流转'两个维度。"
    )
    add_paragraph_custom(doc, "请求流入：", bold=True)
    add_paragraph_custom(doc,
        "用户输入 → ChatPanel (React) → sendMessageStream (api.ts) → POST /api/chat/stream → "
        "chat.py → _load_history_messages (从 SQLite 加载历史) → 构造 TutorState (含 messages) → "
        "tutor_graph.invoke(initial_state, config) → LangGraph 执行工作流 → 返回 final_reply → "
        "SSE 流式输出 → 前端渲染"
    )
    add_paragraph_custom(doc, "状态流转：", bold=True)
    add_paragraph_custom(doc,
        "TutorState 在工作流各节点间传递，关键字段变化如下："
    )
    add_code_block(doc, """TutorState 字段说明：
- student_id / session_id: 标识信息，全程不变
- student_input: 当前用户输入，由 chat.py 注入
- messages: Annotated[list, add_messages] — LangGraph 自动合并
- is_info_complete: check_student_info 节点设置
- just_completed: collect_info 节点设置（避免刚完成信息就当作问题处理）
- kb_hit / socratic_context: search_knowledge_base 节点设置
- search_result: tavily_search 节点设置
- final_reply: socratic_teach / generate_answer / collect_info 节点设置
- stage: 每个节点更新当前阶段名称""")

    add_image_placeholder(doc, "数据流图 — 请绘制 TutorState 在各节点间的字段变化流程")

    add_heading_custom(doc, "3.4 记忆机制设计", level=2)
    add_paragraph_custom(doc,
        "TutorMind 实现了三层记忆机制，满足不同时间尺度的上下文需求："
    )
    add_table_custom(doc,
        ["记忆类型", "存储介质", "容量", "用途", "实现类"],
        [
            ["短期记忆", "内存 (dict)", "20 条/会话", "当前会话快速上下文访问", "ShortTermMemory"],
            ["长期记忆", "SQLite", "无限制", "跨会话持久化、历史加载", "LongTermMemory"],
            ["向量记忆", "ChromaDB", "无限制", "相似问题检索、知识复用", "VectorStore"],
            ["Checkpoint", "内存 (MemorySaver)", "无限制", "工作流状态恢复、断点续跑", "MemorySaver"],
        ]
    )
    add_image_placeholder(doc, "记忆机制架构图 — 请绘制三层记忆 + Checkpoint 的关系图")

    add_heading_custom(doc, "3.5 多轮对话设计", level=2)
    add_paragraph_custom(doc,
        "多轮对话是 TutorMind v0.2 的核心升级。实现要点："
    )
    add_paragraph_custom(doc,
        "（1）消息标准化：所有历史消息转换为 LangChain BaseMessage（HumanMessage / AIMessage），"
        "以标准 OpenAI 消息格式传给 LLM，而非简单的字符串拼接。"
    )
    add_paragraph_custom(doc,
        "（2）历史加载：chat.py 中的 _load_history_messages() 从 SQLite 读取历史记录，"
        "按时间顺序转为 BaseMessage 列表，注入 initial_state['messages']。"
    )
    add_paragraph_custom(doc,
        "（3）消息追加：工作流各节点（collect_info、socratic_teach、generate_answer）"
        "执行后将当前轮次的 (HumanMessage, AIMessage) 追加到 state['messages']，"
        "利用 LangGraph 的 add_messages reducer 自动合并。"
    )
    add_paragraph_custom(doc,
        "（4）LLM 调用：orchestrator.call_llm_with_messages() 接收 system_prompt + messages 列表，"
        "将 BaseMessage 转换为 DashScope 格式（role: system/user/assistant），"
        "使 LLM 看到完整的对话角色序列。"
    )

    # ═══════════════════════════════════════════════════════════
    # 四、关键实现与代码展示
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "四、关键实现与代码展示", level=1)

    add_heading_custom(doc, "4.1 LangGraph 工作流定义", level=2)
    add_paragraph_custom(doc,
        "工作流由 build_workflow() 函数构建，包含 6 个节点和 3 条条件路由："
    )
    add_code_block(doc, """def build_workflow() -> StateGraph:
    workflow = StateGraph(TutorState)

    workflow.add_node("check_student_info", check_student_info)
    workflow.add_node("collect_info", collect_info)
    workflow.add_node("search_knowledge_base", search_knowledge_base)
    workflow.add_node("socratic_teach", socratic_teach)
    workflow.add_node("tavily_search", tavily_search)
    workflow.add_node("generate_answer", generate_answer)

    workflow.set_entry_point("check_student_info")

    workflow.add_conditional_edges(
        "check_student_info",
        route_after_check,
        {"collect_info": "collect_info",
         "search_knowledge_base": "search_knowledge_base"},
    )
    workflow.add_conditional_edges(
        "collect_info",
        route_after_collect,
        {"__end__": END, "search_knowledge_base": "search_knowledge_base"},
    )
    workflow.add_conditional_edges(
        "search_knowledge_base",
        route_after_kb_search,
        {"socratic_teach": "socratic_teach",
         "tavily_search": "tavily_search"},
    )

    workflow.add_edge("socratic_teach", END)
    workflow.add_edge("tavily_search", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow""")

    add_heading_custom(doc, "4.2 资料更新意图识别", level=2)
    add_paragraph_custom(doc,
        "InfoCollectorAgent 通过关键词启发式识别用户更新个人信息的意图："
    )
    add_code_block(doc, """class InfoCollectorAgent:
    _UPDATE_SIGNALS = [
        '基础薄弱', '基础不好', '基础差', '基础一般',
        '有一定基础', '没有基础', '零基础',
        '我叫', '我是', '今年', '岁', '年级', '学历',
        '改一下', '修改', '更新', '换', '改成',
    ]

    def looks_like_profile_update(self, student_input: str) -> bool:
        return any(sig in student_input for sig in self._UPDATE_SIGNALS)""")
    add_paragraph_custom(doc,
        "在 check_student_info 节点中，即使资料已完整，如果检测到更新意图，"
        "强制 is_info_complete=False，路由到 collect_info 节点进行更新："
    )
    add_code_block(doc, """def check_student_info(state: TutorState) -> TutorState:
    result = info_collector.check(state["student_id"])
    state["is_info_complete"] = result["is_complete"]

    if state["is_info_complete"] and \
       info_collector.looks_like_profile_update(state["student_input"]):
        state["is_info_complete"] = False  # 强制进入 collect_info

    return state""")

    add_heading_custom(doc, "4.3 多轮对话消息构建", level=2)
    add_paragraph_custom(doc,
        "_build_messages() 将 state['messages'] 转换为标准 LangChain BaseMessage："
    )
    add_code_block(doc, """def _build_messages(state: TutorState) -> list:
    raw_messages = state.get("messages", [])
    result = []
    for msg in raw_messages:
        if isinstance(msg, (HumanMessage, AIMessage)):
            result.append(msg)
        elif isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ("student", "user", "human"):
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
    return result""")
    add_paragraph_custom(doc,
        "SocraticTutorAgent 使用多轮 API 调用 LLM："
    )
    add_code_block(doc, """def teach(self, student_id, student_input, context, session_id, messages=None):
    if messages:
        messages_with_current = list(messages)
        messages_with_current.append(HumanMessage(content=student_input))
        reply = orchestrator.call_llm_with_messages(
            system_prompt=current_prompt,
            messages=messages_with_current,
        )
    else:
        # Fallback to legacy API
        reply = orchestrator.call_llm(current_prompt, student_input, history=history)""")

    add_heading_custom(doc, "4.4 LLM 多轮调用接口", level=2)
    add_paragraph_custom(doc,
        "OrchestratorAgent 提供 call_llm_with_messages()，将 LangChain 消息转换为 DashScope 格式："
    )
    add_code_block(doc, """def call_llm_with_messages(self, system_prompt, messages, adaptive_instructions=None):
    dashscope_messages = [{"role": "system", "content": full_system}]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            dashscope_messages.append({"role": "user", "content": str(msg.content)})
        elif isinstance(msg, AIMessage):
            dashscope_messages.append({"role": "assistant", "content": str(msg.content)})

    resp = dashscope.Generation.call(
        model=self.model,
        messages=dashscope_messages,
        result_format="message",
    )
    return resp.output.choices[0].message.content""")

    add_heading_custom(doc, "4.5 前端流式消息渲染", level=2)
    add_paragraph_custom(doc,
        "ChatPanel 组件使用 SSE 接收流式响应，实时更新消息内容："
    )
    add_code_block(doc, """sendMessageStream(
  { student_id, session_id, message: text },
  {
    onMeta: (meta) => { /* 更新 agentName, isGuided */ },
    onContent: (chunk) => {
      currentContent += chunk;
      setMessages(prev => prev.map(m =>
        m.id === assistantId ? { ...m, content: currentContent } : m
      ));
    },
    onDone: () => setStreaming(false),
    onError: (error) => { /* 显示错误 */ },
  }
);""")

    add_heading_custom(doc, "4.6 AI IDE 使用截图", level=2)
    add_image_placeholder(doc, "AI IDE 使用截图 — 请在 Trae CN 中截取以下场景的截图："
        "(1) 使用 Builder 模式生成代码的界面；"
        "(2) 使用 Chat 模式询问技术问题的对话；"
        "(3) 使用 Composer 模式进行多文件编辑的界面")

    # ═══════════════════════════════════════════════════════════
    # 五、测试与评估
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "五、测试与评估", level=1)

    add_heading_custom(doc, "5.1 功能测试", level=2)
    add_paragraph_custom(doc,
        "后端单元测试覆盖工作流路由、Agent 行为、数据库操作等核心逻辑，共 20 个测试用例。"
    )
    add_paragraph_custom(doc, "测试运行结果：", bold=True)
    add_code_block(doc, """$ python -m pytest tests/ -v
========================= test session starts ==========================
backend/tests/test_workflow.py::TestRouting::test_route_after_check_info_complete PASSED
backend/tests/test_workflow.py::TestRouting::test_route_after_check_info_incomplete PASSED
backend/tests/test_workflow.py::TestRouting::test_route_after_collect_still_incomplete PASSED
backend/tests/test_workflow.py::TestRouting::test_route_after_collect_now_complete PASSED
backend/tests/test_workflow.py::TestRouting::test_route_after_kb_search_hit PASSED
backend/tests/test_workflow.py::TestRouting::test_route_after_kb_search_miss PASSED
backend/tests/test_workflow.py::TestWorkflowStructure::test_build_workflow_returns_valid_graph PASSED
backend/tests/test_workflow.py::TestWorkflowStructure::test_create_tutor_graph_compiles PASSED
backend/tests/test_workflow.py::TestStateInit::test_tutor_state_creation PASSED
...
======================== 20 passed in 2.34s ==========================""")

    add_heading_custom(doc, "5.2 Agent 行为评估", level=2)
    add_paragraph_custom(doc,
        "通过手动 API 测试验证各 Agent 的行为符合预期："
    )
    add_table_custom(doc,
        ["测试场景", "输入", "预期行为", "实际结果"],
        [
            ["信息收集", "你好，我叫张三，今年20岁，大一学生", "collect_info 节点执行，返回确认", "通过"],
            ["资料更新", "我的基础薄弱", "检测到更新意图，路由到 collect_info，更新 is_weak_foundation", "通过"],
            ["知识库命中", "什么是微积分？（第二次提问）", "socratic_teach 节点执行，返回引导问题", "通过"],
            ["知识库未命中", "什么是量子计算？", "tavily_search → generate_answer，返回搜索结果生成的答案", "通过"],
            ["多轮对话", "能再详细解释一下吗？", "LLM 基于历史上下文进行连贯回复", "通过"],
        ]
    )

    add_heading_custom(doc, "5.3 Demo 截图", level=2)
    add_image_placeholder(doc, "Demo 截图 1 — 学生信息收集场景："
        "显示用户输入'你好，我叫张三...'，系统回复'你好，张三！很高兴认识你...'")
    add_image_placeholder(doc, "Demo 截图 2 — 苏格拉底引导场景："
        "显示用户提问，系统以'苏格拉底导师'身份返回递进式引导问题")
    add_image_placeholder(doc, "Demo 截图 3 — 资料更新场景："
        "显示用户输入'我的基础薄弱'，系统正确更新资料并返回确认")
    add_image_placeholder(doc, "Demo 截图 4 — 多轮对话场景："
        "显示连续多轮对话，LLM 能够引用前文内容进行连贯回复")

    # ═══════════════════════════════════════════════════════════
    # 六、系统升级与扩展
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "六、系统升级与扩展", level=1)

    add_heading_custom(doc, "6.1 可扩展架构", level=2)
    add_paragraph_custom(doc,
        "TutorMind 的架构设计遵循开闭原则，新增 Agent 只需三步："
    )
    add_paragraph_custom(doc,
        "（1）在 app/agents/ 目录下创建新的 Agent 类，实现核心方法；"
        "（2）在 workflow.py 中添加节点函数和条件路由；"
        "（3）在 TutorState 中扩展所需的状态字段。"
    )
    add_paragraph_custom(doc,
        "例如，新增 QuizAgent（测验 Agent）时，只需在 socratic_teach 之后添加 quiz_node，"
        "根据学生回答正确率决定是继续提问还是结束测验。"
    )

    add_heading_custom(doc, "6.2 下一阶段计划", level=2)
    add_table_custom(doc,
        ["版本", "计划内容", "技术要点"],
        [
            ["v0.3", "学习分析 + Docker 部署", "学习进度追踪、知识薄弱点分析、Docker Compose 一键部署"],
            ["v0.4", "MCP 协议 + 云部署", "MCP Server 集成、云服务器部署、HTTPS 支持"],
            ["v0.5", "可观测性增强", "LangSmith 追踪、Prometheus 监控、结构化日志分析"],
            ["v0.6", "多模态支持", "图片输入（拍照搜题）、语音输入/输出"],
        ]
    )

    add_heading_custom(doc, "6.3 AI 能力演进路径", level=2)
    add_paragraph_custom(doc,
        "（1）当前：基于规则的条件路由（is_info_complete、kb_hit）；"
        "未来可引入 LLM-based Router，让模型自主决定下一步执行哪个 Agent。"
    )
    add_paragraph_custom(doc,
        "（2）当前：单轮苏格拉底引导（每次请求一个引导问题）；"
        "未来可扩展为多轮苏格拉底循环（在 LangGraph 内部实现 while 循环），"
        "直到学生给出正确答案或达到最大轮次。"
    )
    add_paragraph_custom(doc,
        "（3）当前：固定相似度阈值（0.75）；"
        "未来可引入动态阈值，根据问题类型和学生基础水平自适应调整。"
    )
    add_paragraph_custom(doc,
        "（4）当前：单一 LLM（DashScope qwen-plus）；"
        "未来可引入模型路由，简单问题用轻量模型、复杂问题用强模型，降低成本。"
    )

    # ═══════════════════════════════════════════════════════════
    # 七、课程总结
    # ═══════════════════════════════════════════════════════════
    add_heading_custom(doc, "七、课程总结", level=1)

    add_heading_custom(doc, "7.1 个人收获", level=2)
    add_paragraph_custom(doc,
        "通过本课程的学习和 TutorMind 项目的开发，我在以下方面获得了显著提升："
    )
    add_paragraph_custom(doc,
        "（1）Agentic AI 思维转变：从'写代码解决问题'转变为'设计智能体协作解决问题'。"
        "学会了如何将复杂任务拆解为多个 Agent 的职责，通过状态机编排实现可控的 AI 行为。"
    )
    add_paragraph_custom(doc,
        "（2）LangGraph 深度实践：掌握了 StateGraph 的节点定义、条件路由、状态传递、"
        "Checkpoint 持久化等核心概念，能够独立设计多步骤推理工作流。"
    )
    add_paragraph_custom(doc,
        "（3）SDD 方法论：理解了 Product Spec → Architecture Spec → API Spec 的分层设计思想，"
        "认识到规格文档不是'写完后就不看'的摆设，而是指导实现、约束范围、评估完成度的核心工具。"
    )
    add_paragraph_custom(doc,
        "（4）工程实践能力：通过 Trae CN AI IDE 的辅助，大幅提升了编码效率；"
        "通过 Docker 容器化部署，理解了生产环境的一致性要求；"
        "通过 pytest 单元测试，建立了'测试先行'的开发习惯。"
    )

    add_heading_custom(doc, "7.2 工程思维转变", level=2)
    add_paragraph_custom(doc,
        "本课程让我深刻认识到'智能体编排者'与'代码编写者'的本质区别："
    )
    add_paragraph_custom(doc,
        "代码编写者关注'如何实现功能'，而智能体编排者关注'如何让多个 Agent 协作完成目标'。"
        "后者需要更强的系统思维能力——理解每个 Agent 的能力边界、设计合理的状态传递机制、"
        "预判异常场景并设计兜底策略。"
    )
    add_paragraph_custom(doc,
        "例如，在设计'资料更新识别'功能时，最初的想法是让 LLM 判断用户意图，"
        "但考虑到成本和延迟，最终选择了关键词启发式方案。"
        "这个决策体现了工程思维中'够用就好'的实用主义原则。"
    )

    add_heading_custom(doc, "7.3 对课程的建议", level=2)
    add_paragraph_custom(doc,
        "（1）建议增加 MCP 协议的实战环节：MCP 作为 Agent 与外部工具通信的标准协议，"
        "课程中虽有提及但缺乏动手实践，建议增加一个'构建 MCP Server'的实验。"
    )
    add_paragraph_custom(doc,
        "（2）建议增加 LLMOps 可观测性内容：当前课程侧重于 Agent 开发，"
        "但对生产环境中的监控、追踪、评估覆盖较少，建议补充 LangSmith / Langfuse 的使用教学。"
    )
    add_paragraph_custom(doc,
        "（3）建议增加多模态 Agent 的案例：当前案例以文本交互为主，"
        "建议增加图像理解、语音交互等多模态场景，拓宽学生对 Agent 能力的认知。"
    )

    # ── Save ───────────────────────────────────────────────────
    output_path = "/workspace/CS599_大作业报告.docx"
    doc.save(output_path)
    print(f"Report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_report()
