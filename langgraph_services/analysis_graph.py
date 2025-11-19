"""
LangGraph状态定义和节点实现
用于AI数据透视助手的分步分析流程
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import pandas as pd
import json


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


class AnalysisState(TypedDict):
    """LangGraph状态定义"""
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
    stream_target: Optional[str]  # 用于指定流式输出的目标（如"step_by_step"或"chat"）


def plan_analysis_task_node(state: AnalysisState) -> AnalysisState:
    """
    任务规划节点
    将用户的数据分析请求转换为具体的计算任务
    """
    from llm_services.analysis_planner import plan_analysis_task
    
    try:
        user_request = state["user_message"]
        file_content = state["file_content"]
        api_key = state["api_key"]
        
        # 调用原有的任务规划函数
        task_plan_dict = plan_analysis_task(user_request, file_content, api_key)
        
        # 将字典转换为TaskPlan对象
        task_plan = TaskPlan(
            task_type=task_plan_dict.get("task_type", "未知任务"),
            columns=task_plan_dict.get("columns", []),
            operations=task_plan_dict.get("operations", []),
            expected_output=task_plan_dict.get("expected_output", "无预期输出")
        )
        
        print(f"任务规划完成: {task_plan.task_type}")
        
        return {
            **state,
            "task_plan": task_plan,
            "current_step": "planning",
            "error": None
        }
    except Exception as e:
        print(f"任务规划节点出错: {str(e)}")
        return {
            **state,
            "error": f"任务规划失败: {str(e)}",
            "current_step": "planning_error"
        }


def process_data_node(state: AnalysisState) -> AnalysisState:
    """
    数据处理节点
    根据任务计划执行具体的数据处理操作
    """
    from llm_services.data_processor import process_data
    
    try:
        task_plan = state["task_plan"]
        file_content = state["file_content"]
        
        # 将TaskPlan转换为字典格式以兼容现有函数
        task_plan_dict = {
            "task_type": task_plan.task_type,
            "columns": task_plan.columns,
            "operations": task_plan.operations,
            "expected_output": task_plan.expected_output
        }
        
        # 调用现有的数据处理函数
        computation_results = process_data(task_plan_dict, file_content)
        
        print(f"数据处理完成，处理结果: {len(computation_results)} 项")
        
        return {
            **state,
            "computation_results": computation_results,
            "current_step": "processing",
            "error": None
        }
    except Exception as e:
        print(f"数据处理节点出错: {str(e)}")
        return {
            **state,
            "error": f"数据处理失败: {str(e)}",
            "current_step": "processing_error"
        }


def generate_report_node(state: AnalysisState) -> AnalysisState:
    """
    报告生成节点
    整合计算结果并生成最终分析报告
    """
    from llm_services.report_generator import generate_report
    
    try:
        task_plan = state["task_plan"]
        computation_results = state["computation_results"]
        api_key = state["api_key"]
        output_as_table = state["output_as_table"]
        
        # 将TaskPlan转换为字典格式
        task_plan_dict = {
            "task_type": task_plan.task_type,
            "columns": task_plan.columns,
            "operations": task_plan.operations,
            "expected_output": task_plan.expected_output
        }
        
        # 调用现有的报告生成函数
        final_report = generate_report(task_plan_dict, computation_results, api_key, output_as_table)
        
        print(f"报告生成完成，报告长度: {len(final_report)} 字符")
        
        return {
            **state,
            "final_report": final_report,
            "current_step": "reporting",
            "error": None
        }
    except Exception as e:
        print(f"报告生成节点出错: {str(e)}")
        return {
            **state,
            "error": f"报告生成失败: {str(e)}",
            "current_step": "reporting_error"
        }


def chat_node(state: AnalysisState) -> AnalysisState:
    """
    聊天节点
    处理普通聊天请求（非分步分析）
    """
    from llm_services.qwen_engine import chat_with_llm_stream
    import asyncio
    
    try:
        user_message = state["user_message"]
        file_content = state["file_content"]
        chat_history = state["chat_history"]
        settings = state["settings"]
        
        # 准备消息列表，包含历史记录和当前查询
        messages = []
        
        # 添加历史记录到消息列表
        for msg in chat_history:
            role = 'user' if msg['role'] == 'user' else 'assistant'
            messages.append({
                'role': role,
                'content': msg['content']
            })
        
        # 如果有文件内容，将其添加到用户消息中
        if file_content:
            user_message = f"请分析以下文件内容：\n\n{file_content}\n\n{user_message}"
        
        # 添加当前查询
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        # 准备模型参数
        model_params = {
            'model': settings.get('modelName', 'qwen-max'),
            'temperature': settings.get('temperature', 0.7),
            'max_tokens': settings.get('maxTokens', 8196),
            'top_p': settings.get('topP', 0.9),
            'frequency_penalty': settings.get('frequencyPenalty', 0.5),
            'api_key': settings.get('apiKey') or state.get('api_key'),
            'base_url': settings.get('baseUrl', None),
            'history': []  # 已经手动处理了历史记录
        }
        
        # 调用模型获取回复
        full_response = ""
        for chunk in chat_with_llm_stream(user_message, **model_params):
            if chunk:
                full_response += chunk
        
        print(f"聊天回复完成，回复长度: {len(full_response)} 字符")
        
        return {
            **state,
            "final_report": full_response,
            "current_step": "chatting",
            "error": None
        }
    except Exception as e:
        print(f"聊天节点出错: {str(e)}")
        return {
            **state,
            "error": f"聊天处理失败: {str(e)}",
            "current_step": "chat_error"
        }


def create_analysis_graph():
    """
    创建分析流程图
    """
    workflow = StateGraph(AnalysisState)
    
    # 添加节点
    workflow.add_node("plan_analysis", plan_analysis_task_node)
    workflow.add_node("process_data", process_data_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("chat", chat_node)
    
    # 为聊天节点添加边
    workflow.add_conditional_edges(
        START,
        route_message,
        {
            "step_by_step": "plan_analysis",
            "chat": "chat"
        }
    )
    
    # 分步分析流程
    workflow.add_edge("plan_analysis", "process_data")
    workflow.add_edge("process_data", "generate_report")
    workflow.add_edge("generate_report", END)
    
    # 聊天流程
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


def create_simple_analysis_graph():
    """
    创建简化的分析流程图（仅分步分析）
    """
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


def run_full_analysis(initial_state: AnalysisState):
    """
    运行完整的分析流程并返回中间结果
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Yields:
        tuple: (step_number, step_name, result)
    """
    # 运行任务规划步骤
    state_after_planning = plan_analysis_task_node(initial_state)
    yield (1, "planning", state_after_planning)
    
    # 运行数据处理步骤
    state_after_processing = process_data_node(state_after_planning)
    yield (2, "processing", state_after_processing)
    
    # 运行报告生成步骤
    final_state = generate_report_node(state_after_processing)
    yield (3, "reporting", final_state)


# 创建全局图实例
analysis_graph = create_analysis_graph()
simple_analysis_graph = create_simple_analysis_graph()