"""
CrewAI implementation for TutorMind multi-agent collaboration.
This layer provides an alternative orchestration approach to complement LangGraph.
"""

import os
from textwrap import dedent

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from langchain_community.llms.tongyi import Tongyi

from app.config import settings
from app.tools.student_profile import (
    get_student_profile,
    save_student_profile,
    has_complete_info,
    get_missing_info_message,
)
from app.tools.kb_search import search_knowledge_base
from app.tools.tavily_tool import tavily_search
from app.tools.foundation_check import get_adaptive_instructions


# ── LLM initialization for CrewAI ──────────────────────────────────────

llm = Tongyi(
    model_name=settings.llm_model,
    dashscope_api_key=settings.dashscope_api_key,
    temperature=0.3,
)


# ── Tool definitions wrapped for CrewAI ──────────────────────────────

@tool
def check_student_info(student_id: str) -> str:
    """Check if a student has all required information collected.
    Returns: Status message about missing information.
    """
    if has_complete_info(student_id):
        profile = get_student_profile(student_id)
        weak = "基础薄弱" if profile and profile.is_weak_foundation else "有一定基础"
        return f"学生信息完整。{weak}。"
    else:
        prompt = get_missing_info_message(student_id)
        return f"学生信息不完整。需要追问：{prompt}"


@tool
def search_similar_questions(question: str) -> str:
    """Search the knowledge base for similar questions from previous sessions.
    Returns: Found similar questions and their answers, or 'not found'.
    """
    result = search_knowledge_base(question)
    if not result["found"]:
        return "知识库中未找到相似问题，需要进行实时搜索。"

    output_lines = ["找到以下相似问题："]
    for i, match in enumerate(result["similar_questions"], 1):
        output_lines.append(f"\n{i}. 相似度: {match['similarity_score']:.2f}")
        output_lines.append(f"问题: {match['question']}")
        output_lines.append(f"历史回答: {match['answer'][:300]}...")
    return "\n".join(output_lines)


@tool
def web_search(query: str) -> str:
    """Search the web for current information about the question.
    Returns: Formatted search results.
    """
    results = tavily_search(query)
    if not results:
        return "搜索未找到任何结果。"
    lines = [f"找到 {len(results)} 条结果:"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n{i}. **{r.get('title', '')}**")
        lines.append(r.get('content', '')[:400] + "...")
    return "\n".join(lines)


@tool
def get_adaptive_style(student_id: str) -> str:
    """Get adaptive teaching instructions based on student's foundation level.
    Returns: Instruction text for the tutor to follow.
    """
    return get_adaptive_instructions(student_id)


# ── Agent Definitions ────────────────────────────────────────────────

def create_info_collector_agent() -> Agent:
    return Agent(
        role="信息收集专家",
        goal=dedent("""
            收集学生的完整基本信息：姓名、年龄、学历、基础水平。
            如果信息不完整，礼貌地追问学生补充缺失信息。
        """),
        backstory=dedent("""
            你是TutorMind系统中专门负责信息收集的专家。
            在学生开始学习之前，你必须确保收集到所有必要的信息。
            你擅长从自然语言中提取出结构化信息并保存。
        """),
        tools=[check_student_info],
        llm=llm,
        verbose=True,
    )


def create_knowledge_retriever_agent() -> Agent:
    return Agent(
        role="知识检索专家",
        goal=dedent("""
            在知识库中检索与学生问题相似的历史问答。
            判断是否存在足够相似的问题可以复用引导路径。
        """),
        backstory=dedent("""
            你精通向量检索技术，能够准确找出语义相似的问题。
            只有相似度超过阈值的结果才会被你认为有效命中。
        """),
        tools=[search_similar_questions],
        llm=llm,
        verbose=True,
    )


def create_socratic_tutor_agent() -> Agent:
    return Agent(
        role="苏格拉底教学专家",
        goal=dedent("""
            通过递进式提问逐步引导学生自己推导出答案，不要直接给出答案。
            根据学生基础水平调整提问步长。
        """),
        backstory=dedent("""
            你是一位深谙苏格拉底教学法的伟大导师。
            你相信最好的教学是引导学生自己发现真理，而不是灌输知识。
            你擅长把一个大问题分解成一系列小问题，每次只问一个问题。
            你会根据学生的回答不断调整提问方向，直到学生自己得出正确结论。
        """),
        tools=[get_adaptive_style],
        llm=llm,
        verbose=True,
    )


def create_search_agent() -> Agent:
    return Agent(
        role="实时搜索专家",
        goal=dedent("""
            在网络上搜索新知识，整理成清晰准确的回答。
            按照学生基础水平调整回答难度和语言风格。
        """),
        backstory=dedent("""
            当知识库中找不到答案时，你负责调用实时搜索获取最新信息。
            你擅长从大量搜索结果中提炼出最核心、最准确的内容。
            你能把复杂的专业知识转换成通俗易懂的语言。
        """),
        tools=[web_search, get_adaptive_style],
        llm=llm,
        verbose=True,
    )


def create_orchestrator_agent() -> Agent:
    return Agent(
        role="系统总协调人",
        goal=dedent("""
            协调各个专家Agent按正确流程完成工作：
            1. 先检查学生信息完整性
            2. 信息完整后进行知识检索
            3. 如果找到相似问题，交给苏格拉底导师引导
            4. 如果没找到，交给搜索Agent获取新知识
            5. 最后汇总结果输出给学生
        """),
        backstory=dedent("""
            你是TutorMind系统的大脑，负责把控整个对话流程。
            你清楚每个专家的职责，并知道什么时候该调用谁。
        """),
        tools=[check_student_info, search_similar_questions],
        llm=llm,
        verbose=True,
    )


def create_tutor_crew() -> Crew:
    """Create the full TutorMind multi-agent crew."""
    info_agent = create_info_collector_agent()
    kb_agent = create_knowledge_retriever_agent()
    socratic_agent = create_socratic_tutor_agent()
    search_agent = create_search_agent()
    orchestrator = create_orchestrator_agent()

    # Define tasks
    info_task = Task(
        description=dedent("""
            检查学生 {student_id} 的信息是否完整。
            如果不完整，生成追问信息。如果完整，确认信息完整。
        """),
        expected_output="学生信息完整性检查结果和缺失提示（如果有）。",
        agent=info_agent,
    )

    knowledge_task = Task(
        description=dedent("""
            对学生问题「{question}」进行知识检索。
            判断是否找到相似度超过阈值的相似问题。
        """),
        expected_output="检索结果：找到相似问题或未找到。",
        agent=kb_agent,
        context=[info_task],
    )

    socratic_task = Task(
        description=dedent("""
            基于知识库中的相似问题，为学生「{student_id}」生成第一个苏格拉底引导提问。
            严格遵守苏格拉底原则：不直接给答案，只提问引导学生自己思考。
            遵循 {student_id} 的自适应教学要求。
        """),
        expected_output="一个清晰的引导问题。",
        agent=socratic_agent,
        context=[info_task, knowledge_task],
    )

    search_task = Task(
        description=dedent("""
            对学生问题「{question}」进行网络搜索。
            根据搜索结果整理出准确清晰的回答。
            遵循学生 {student_id} 的自适应教学要求调整语言风格。
        """),
        expected_output="结构化的回答。",
        agent=search_agent,
        context=[info_task, knowledge_task],
    )

    final_task = Task(
        description=dedent("""
            汇总各Agent的工作结果，生成最终输出给学生。
            当前学生问题是：{question}
        """),
        expected_output="最终回复学生的文字。",
        agent=orchestrator,
        context=[info_task, knowledge_task],
    )

    # Create crew with sequential process
    crew = Crew(
        agents=[info_agent, kb_agent, socratic_agent, search_agent, orchestrator],
        tasks=[info_task, knowledge_task, socratic_task, search_task, final_task],
        process=Process.sequential,
        verbose=1 if settings.debug else 0,
    )

    return crew


def run_tutor_workflow(student_id: str, question: str) -> str:
    """
    Run the full multi-agent workflow via CrewAI.
    Returns the final answer string.
    """
    crew = create_tutor_crew()
    result = crew.kickoff(inputs={
        "student_id": student_id,
        "question": question,
    })
    return result