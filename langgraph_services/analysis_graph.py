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
    from llm_services.enhanced_analysis_planner import plan_analysis_task
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始任务规划节点处理")
    
    try:
        user_request = state["user_message"]
        file_content = state["file_content"]
        api_key = state["api_key"]
        
        # 获取历史规划记录（转换为字典格式供增强规划器使用）
        plan_history = state.get("plan_history", [])
        plan_history_dicts = []
        for plan in plan_history:
            if hasattr(plan, 'dict'):
                plan_history_dicts.append(plan.dict())
            elif isinstance(plan, dict):
                plan_history_dicts.append(plan)
            else:
                # 如果是其他格式，尝试转换
                plan_dict = {}
                if hasattr(plan, '__dict__'):
                    plan_dict = plan.__dict__.copy()
                plan_history_dicts.append(plan_dict)
        
        logger.info(f"任务规划 - 用户请求: {user_request[:50]}..." if len(user_request) > 50 else f"任务规划 - 用户请求: {user_request}")
        logger.info(f"任务规划 - 文件内容长度: {len(file_content) if file_content else 0}")
        logger.info(f"任务规划 - 历史规划数量: {len(plan_history_dicts)}")
        
        # 调用增强的任务规划函数，传入历史规划记录
        task_plan_dict = plan_analysis_task(user_request, file_content, api_key, plan_history_dicts)
        
        # 将字典转换为TaskPlan对象
        task_plan = TaskPlan(
            task_type=task_plan_dict.get("task_type", "未知任务"),
            columns=task_plan_dict.get("columns", []),
            operations=task_plan_dict.get("operations", []),
            expected_output=task_plan_dict.get("expected_output", "无预期输出")
        )
        
        # 更新计划历史
        plan_history = state.get("plan_history", [])
        plan_history.append(task_plan)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time}] 任务规划完成: {task_plan.task_type}, 耗时: {duration:.2f}秒")
        
        return {
            **state,
            "task_plan": task_plan,
            "current_step": "planning",
            "error": None,
            "processed": True,
            "needs_replanning": False,
            "plan_history": plan_history
        }
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 任务规划节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        return {
            **state,
            "error": f"任务规划失败: {str(e)}",
            "current_step": "planning_error",
            "processed": True
        }


"""
LangGraph状态定义和图构建
用于AI数据透视助手的动态规划分析流程
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import pandas as pd
import json
import logging
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


def should_continue_iteration(state: AnalysisState) -> str:
    """
    决定是否继续迭代的条件函数
    """
    from .node_handlers import observe_and_evaluate_node  # 用于类型引用
    
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)
    needs_replanning = state.get("needs_replanning", False)
    observation = state.get("observation")
    
    logger.info(f"条件函数检查 - 当前迭代: {iteration_count}, 最大迭代: {max_iterations}")
    logger.info(f"条件函数检查 - 需要重新规划: {needs_replanning}")
    if observation:
        logger.info(f"条件函数检查 - 观察质量评分: {observation.quality_score}, 反馈: {observation.feedback[:50] if observation.feedback else 'N/A'}...")
    
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
    from .node_handlers import plan_analysis_task_node, process_data_node, observe_and_evaluate_node, replan_analysis_task_node, generate_report_node
    return create_analysis_graph()

def get_chat_graph():
    from .node_handlers import chat_node
    return create_chat_graph()

def get_conditional_graph():
    from .node_handlers import plan_analysis_task_node, process_data_node, observe_and_evaluate_node, replan_analysis_task_node, generate_report_node, chat_node
    return create_conditional_graph()


def process_data_node(state: AnalysisState) -> AnalysisState:
    """
    数据处理节点
    根据任务计划执行具体的数据处理操作
    """
    from llm_services.data_processor import process_data
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始数据处理节点处理")
    
    try:
        task_plan = state["task_plan"]
        file_content = state["file_content"]
        
        logger.info(f"数据处理 - 任务类型: {task_plan.task_type}")
        logger.info(f"数据处理 - 操作数量: {len(task_plan.operations) if task_plan.operations else 0}")
        logger.info(f"数据处理 - 文件内容长度: {len(file_content) if file_content else 0}")
        
        # 将TaskPlan转换为字典格式以兼容现有函数
        task_plan_dict = {
            "task_type": task_plan.task_type,
            "columns": task_plan.columns,
            "operations": task_plan.operations,
            "expected_output": task_plan.expected_output
        }
        
        # 调用现有的数据处理函数
        computation_results = process_data(task_plan_dict, file_content)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time}] 数据处理完成，处理结果: {len(computation_results)} 项, 耗时: {duration:.2f}秒")
        
        return {
            **state,
            "computation_results": computation_results,
            "current_step": "processing",
            "error": None,
            "processed": True
        }
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 数据处理节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        return {
            **state,
            "error": f"数据处理失败: {str(e)}",
            "current_step": "processing_error",
            "processed": True
        }


def observe_and_evaluate_node(state: AnalysisState) -> AnalysisState:
    """
    观察和评估节点
    评估执行结果并决定是否需要重新规划
    """
    from llm_services.observer_evaluator import evaluate_analysis_results, should_replan_analysis
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始观察和评估节点处理")
    logger.info(f"观察节点 - 当前迭代: {state.get('iteration_count', 0)}")
    logger.info(f"观察节点 - 任务计划类型: {state.get('task_plan', {}).task_type if hasattr(state.get('task_plan'), 'task_type') else 'N/A'}")
    logger.info(f"观察节点 - 计算结果数量: {len(state.get('computation_results', {}))}")
    
    try:
        task_plan = state["task_plan"]
        computation_results = state["computation_results"]
        user_message = state["user_message"]
        api_key = state["api_key"]
        settings = state["settings"]
        
        # 将TaskPlan对象转换为字典格式，以便observer_evaluator模块处理
        if hasattr(task_plan, 'dict') and callable(getattr(task_plan, 'dict')):
            task_plan_dict = task_plan.dict()
        elif hasattr(task_plan, '__dict__'):
            task_plan_dict = task_plan.__dict__
        else:
            task_plan_dict = task_plan
        
        # 使用新的评估模块进行分析结果评估
        observation = evaluate_analysis_results(
            task_plan=task_plan_dict,
            computation_results=computation_results,
            user_message=user_message,
            api_key=api_key,
            settings=settings
        )
        
        # 根据观察结果判断是否需要重新规划
        needs_replanning = should_replan_analysis(observation)
        
        logger.info(f"评估完成 - 质量评分: {observation.quality_score}, 需要重新规划: {needs_replanning}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time}] 观察和评估完成，质量评分: {observation.quality_score}, 需要重新规划: {needs_replanning}, 耗时: {duration:.2f}秒")
        
        return {
            **state,
            "observation": observation,
            "current_step": "observing",
            "error": None,
            "processed": True,
            "needs_replanning": needs_replanning,
            "iteration_count": state.get("iteration_count", 0)  # 保持当前迭代计数
        }
            
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 观察和评估节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        # 即使评估出错，也创建一个基本的观察结果并标记需要重新规划
        observation = Observation(
            results=state.get("computation_results", {}),
            quality_score=0.0,
            feedback=f"评估过程中发生错误: {str(e)}",
            success=False,
            next_actions=["重新规划分析任务"]
        )
        return {
            **state,
            "observation": observation,
            "error": f"观察和评估失败: {str(e)}",
            "current_step": "observing_error",
            "processed": True,
            "needs_replanning": True
        }


def generate_report_node(state: AnalysisState) -> AnalysisState:
    """
    报告生成节点
    整合计算结果并生成最终分析报告
    """
    from llm_services.report_generator import generate_report
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始报告生成节点处理")
    
    try:
        task_plan = state["task_plan"]
        computation_results = state["computation_results"]
        api_key = state["api_key"]
        output_as_table = state["output_as_table"]
        
        logger.info(f"报告生成 - 任务类型: {task_plan.task_type if task_plan else 'N/A'}")
        logger.info(f"报告生成 - 计算结果项数: {len(computation_results) if computation_results else 0}")
        logger.info(f"报告生成 - 输出表格模式: {output_as_table}")
        
        # 将TaskPlan转换为字典格式
        task_plan_dict = {
            "task_type": task_plan.task_type,
            "columns": task_plan.columns,
            "operations": task_plan.operations,
            "expected_output": task_plan.expected_output
        }
        
        # 调用现有的报告生成函数
        final_report = generate_report(task_plan_dict, computation_results, api_key, output_as_table)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time}] 报告生成完成，报告长度: {len(final_report)} 字符, 耗时: {duration:.2f}秒")
        
        return {
            **state,
            "final_report": final_report,
            "current_step": "reporting",
            "error": None,
            "processed": True
        }
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 报告生成节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        return {
            **state,
            "error": f"报告生成失败: {str(e)}",
            "current_step": "reporting_error",
            "processed": True
        }


def should_continue_iteration(state: AnalysisState) -> str:
    """
    决定是否继续迭代的条件函数
    """
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)
    needs_replanning = state.get("needs_replanning", False)
    observation = state.get("observation")
    
    logger.info(f"条件函数检查 - 当前迭代: {iteration_count}, 最大迭代: {max_iterations}")
    logger.info(f"条件函数检查 - 需要重新规划: {needs_replanning}")
    if observation:
        logger.info(f"条件函数检查 - 观察质量评分: {observation.quality_score}, 反馈: {observation.feedback[:50] if observation.feedback else 'N/A'}...")
    
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
    from llm_services.qwen_engine import chat_with_llm_stream
    import asyncio
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始聊天节点处理")
    
    try:
        user_message = state["user_message"]
        file_content = state["file_content"]
        chat_history = state["chat_history"]
        settings = state["settings"]
        
        logger.info(f"聊天 - 用户消息: {user_message[:50]}..." if len(user_message) > 50 else f"聊天 - 用户消息: {user_message}")
        logger.info(f"聊天 - 文件内容长度: {len(file_content) if file_content else 0}")
        logger.info(f"聊天 - 历史记录数量: {len(chat_history)}")
        
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
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"[{end_time}] 聊天回复完成，回复长度: {len(full_response)} 字符, 耗时: {duration:.2f}秒")
        
        return {
            **state,
            "final_reply": full_response,
            "current_step": "chatting",
            "error": None,
            "processed": True
        }
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 聊天节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        return {
            **state,
            "error": f"聊天处理失败: {str(e)}",
            "current_step": "chat_error",
            "processed": True
        }


def create_analysis_graph():
    """
    创建分析流程图（使用动态规划图）
    """
    return create_dynamic_analysis_graph()


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
    from .node_handlers import plan_analysis_task_node, process_data_node, observe_and_evaluate_node, replan_analysis_task_node, generate_report_node
    return create_analysis_graph()

def get_chat_graph():
    from .node_handlers import chat_node
    return create_chat_graph()

def get_conditional_graph():
    from .node_handlers import plan_analysis_task_node, process_data_node, observe_and_evaluate_node, replan_analysis_task_node, generate_report_node, chat_node
    return create_conditional_graph()