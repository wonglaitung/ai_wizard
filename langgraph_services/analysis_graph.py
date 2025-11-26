"""
LangGraph状态定义和节点实现
用于AI数据透视助手的动态规划分析流程
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import pandas as pd
import json
import logging
import os
from datetime import datetime


logger = logging.getLogger(__name__)


class Message(BaseModel):
    """消息类型定义"""
    role: str = Field(description="消息角色: user, ai, system")
    content: str = Field(description="消息内容")


class TaskPlan(BaseModel):
    """任务计划定义"""
    task_type: str = Field(description="任务类型")
    columns: List[str] = Field(description="需要分析的列名列表")
    operations: List[Dict[str, Any]] = Field(description="需要执行的操作列表")
    expected_output: str = Field(description="预期的输出结果描述")


class Observation(BaseModel):
    """观察结果定义"""
    results: Dict[str, Any] = Field(description="执行结果")
    quality_score: float = Field(description="结果质量评分(0-1)")
    feedback: str = Field(description="结果反馈")
    success: bool = Field(description="执行是否成功")
    next_actions: List[str] = Field(description="建议的下一步操作")


# 定义动态规划状态类型
class AnalysisState(TypedDict):
    """动态分析流程状态定义"""
    user_message: str
    file_content: str
    chat_history: List[Dict[str, str]]
    settings: Dict[str, Any]
    output_as_table: bool
    task_plan: Optional[TaskPlan]
    computation_results: Optional[Dict[str, Any]]
    final_report: Optional[str]
    current_step: str
    error: Optional[str]
    api_key: Optional[str]
    processed: bool  # 标记是否已处理
    iteration_count: int  # 迭代次数
    max_iterations: int  # 最大迭代次数
    observation: Optional[Observation]  # 当前观察结果
    needs_replanning: bool  # 是否需要重新规划
    plan_history: List[TaskPlan]  # 历史计划


class ChatState(TypedDict):
    """聊天流程状态定义"""
    user_message: str
    file_content: str
    chat_history: List[Dict[str, str]]
    settings: Dict[str, Any]
    output_as_table: bool
    final_reply: Optional[str]
    current_step: str
    error: Optional[str]
    api_key: Optional[str]
    processed: bool  # 标记是否已处理


def plan_analysis_task_node(state: AnalysisState) -> AnalysisState:
    """
    任务规划节点
    将用户的数据分析请求转换为具体的计算任务
    """
    # 此函数已在 node_handlers.py 中实现
    from .node_handlers import plan_analysis_task_node as _plan_analysis_task_node
    return _plan_analysis_task_node(state)


def process_data_node(state: AnalysisState) -> AnalysisState:
    """
    数据处理节点
    根据任务计划执行具体的数据处理操作
    """
    # 此函数已在 node_handlers.py 中实现
    from .node_handlers import process_data_node as _process_data_node
    return _process_data_node(state)


def observe_and_evaluate_node(state: AnalysisState) -> AnalysisState:
    """
    观察和评估节点
    评估执行结果并决定是否需要重新规划
    """
    # 此函数已在 node_handlers.py 中实现
    from .node_handlers import observe_and_evaluate_node as _observe_and_evaluate_node
    return _observe_and_evaluate_node(state)


def generate_report_node(state: AnalysisState) -> AnalysisState:
    """
    报告生成节点
    整合计算结果并生成最终分析报告
    """
    # 此函数已在 node_handlers.py 中实现
    from .node_handlers import generate_report_node as _generate_report_node
    return _generate_report_node(state)


def should_continue_iteration(state: AnalysisState) -> str:
    """
    决定是否继续迭代的条件函数
    """
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)
    needs_replanning = state.get("needs_replanning", False)
    observation = state.get("observation")
    
    # 设置质量评分阈值，超过此值则认为结果足够好，可以提前终止
    quality_threshold = float(os.getenv('QUALITY_THRESHOLD', 0.85))
    
    logger.info(f"条件函数检查 - 当前迭代: {iteration_count}, 最大迭代: {max_iterations}")
    logger.info(f"条件函数检查 - 需要重新规划: {needs_replanning}")
    if observation:
        logger.info(f"条件函数检查 - 观察质量评分: {observation.quality_score}, 质量阈值: {quality_threshold}, 反馈: {observation.feedback[:50] if observation.feedback else 'N/A'}...")
    
    # 检查是否质量评分已满足要求，如果是则提前终止迭代
    if observation and observation.quality_score >= quality_threshold:
        logger.info(f"质量评分 {observation.quality_score} >= {quality_threshold}，满足要求，提前终止迭代")
        return "finish"
    
    # 如果需要重新规划且未超过最大迭代次数，则继续
    if needs_replanning and iteration_count < max_iterations:
        logger.info(f"迭代 {iteration_count + 1}/{max_iterations} - 需要重新规划")
        return "continue"
    else:
        logger.info(f"迭代结束 - 当前迭代: {iteration_count}, 最大迭代: {max_iterations}, 需要重新规划: {needs_replanning}")
        return "finish"


def create_dynamic_analysis_graph():
    """
    创建动态规划分析流程图
    实现规划 → 执行 → 观察 → 重新规划的循环
    """
    # 导入在 node_handlers 中定义的函数
    from .node_handlers import plan_analysis_task_node, process_data_node, observe_and_evaluate_node, replan_analysis_task_node, generate_report_node
    
    workflow = StateGraph(AnalysisState)
    
    # 添加节点
    workflow.add_node("plan_analysis", plan_analysis_task_node)
    workflow.add_node("process_data", process_data_node)
    workflow.add_node("observe_and_evaluate", observe_and_evaluate_node)
    workflow.add_node("replan_analysis", replan_analysis_task_node)
    workflow.add_node("generate_report", generate_report_node)
    
    # 设置入口点
    workflow.add_edge(START, "plan_analysis")
    
    # 基本流程: 规划 -> 执行 -> 观察
    workflow.add_edge("plan_analysis", "process_data")
    workflow.add_edge("process_data", "observe_and_evaluate")
    
    # 根据观察结果决定是否重新规划
    workflow.add_conditional_edges(
        "observe_and_evaluate",
        should_continue_iteration,
        {
            "continue": "replan_analysis",  # 需要重新规划
            "finish": "generate_report"     # 完成分析
        }
    )
    
    # 重新规划后回到执行阶段
    workflow.add_edge("replan_analysis", "process_data")
    
    # 最终生成报告
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()


def create_simple_analysis_graph():
    """
    创建简化的分析流程图（仅分步分析，保持向后兼容）
    """
    from .node_handlers import plan_analysis_task_node, process_data_node, generate_report_node
    
    workflow = StateGraph(AnalysisState)
    
    # 添加节点
    workflow.add_node("plan_analysis", plan_analysis_task_node)
    workflow.add_node("process_data", process_data_node)
    workflow.add_node("generate_report", generate_report_node)
    
    # 定义边
    workflow.add_edge(START, "plan_analysis")
    workflow.add_edge("plan_analysis", "process_data")
    workflow.add_edge("process_data", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()


def create_analysis_graph():
    """
    创建分析流程图（现在使用动态规划图作为默认）
    """
    return create_dynamic_analysis_graph()





def chat_node(state: ChatState) -> ChatState:
    """
    聊天节点
    处理普通聊天请求（非分步分析）
    """
    # 此函数已在 node_handlers.py 中实现
    from .node_handlers import chat_node as _chat_node
    return _chat_node(state)


def create_chat_graph():
    """
    创建聊天流程图
    """
    from .node_handlers import chat_node
    
    workflow = StateGraph(ChatState)
    
    # 添加节点
    workflow.add_node("chat", chat_node)
    
    # 设置入口点和流程
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    return workflow.compile()


def route_message(state):
    """
    决定消息路由的函数
    """
    # 如果用户明确要求分步分析，或者有文件内容，或者用户消息中包含分析相关关键词，则进行分步分析
    needs_step_by_step = (
        state.get("file_content") and state["file_content"] != '' or
        any(keyword in state["user_message"].lower() for keyword in 
            ['分析', '统计', '计算', '数据透视', '报表', '趋势', '对比', '步骤', 'step by step'])
    )
    return "step_by_step" if needs_step_by_step else "chat"


def create_conditional_graph():
    """
    创建条件路由图（使用外部路由逻辑）
    """
    from langgraph.graph import END
    
    def route_and_execute(state: AnalysisState):
        """
        根据条件路由到不同的图
        """
        # 延迟导入以避免循环导入
        from .node_handlers import plan_analysis_task_node, process_data_node, generate_report_node, chat_node
        
        # 动态获取图实例以避免循环导入
        analysis_graph_instance = get_analysis_graph()
        chat_graph_instance = get_chat_graph()
        
        needs_step_by_step = (
            state.get("file_content") and state["file_content"] != '' or
            any(keyword in state["user_message"].lower() for keyword in 
                ['分析', '统计', '计算', '数据透视', '报表', '趋势', '对比', '步骤', 'step by step'])
        )
        
        if needs_step_by_step:
            # 执行分析图
            result = analysis_graph_instance.invoke(state)
            return result
        else:
            # 对于聊天，需要将AnalysisState转换为ChatState
            chat_state: ChatState = {
                "user_message": state["user_message"],
                "file_content": state["file_content"],
                "chat_history": state["chat_history"],
                "settings": state["settings"],
                "output_as_table": state["output_as_table"],
                "final_reply": None,
                "current_step": "initial",
                "error": None,
                "api_key": state["api_key"],
                "processed": False
            }
            result = chat_graph_instance.invoke(chat_state)
            # 将ChatState结果转换回AnalysisState格式
            return {
                **state,
                "final_report": result.get("final_reply"),
                "current_step": result.get("current_step"),
                "error": result.get("error"),
                "processed": result.get("processed", False)
            }
    
    return route_and_execute





def run_full_analysis(initial_state: AnalysisState):
    """
    运行完整的分析流程并返回中间结果
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Yields:
        tuple: (step_number, step_name, result)
    """
    from .node_handlers import plan_analysis_task_node, process_data_node, generate_report_node
    
    # 运行任务规划步骤
    state_after_planning = plan_analysis_task_node(initial_state)
    yield (1, "planning", state_after_planning)
    
    # 运行数据处理步骤
    state_after_processing = process_data_node(state_after_planning)
    yield (2, "processing", state_after_processing)
    
    # 运行报告生成步骤
    final_state = generate_report_node(state_after_processing)
    yield (3, "reporting", final_state)



# 延迟初始化图实例以避免循环导入
def get_analysis_graph():
    from .node_handlers import replan_analysis_task_node  # 确保导入replan_analysis_task_node
    return create_analysis_graph()

def get_chat_graph():
    return create_chat_graph()

def get_conditional_graph():
    return create_conditional_graph()
