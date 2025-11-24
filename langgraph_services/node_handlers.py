"""
节点处理器模块
包含分析流程中的各种节点实现
"""

from typing import Dict, Any
from .analysis_graph import AnalysisState, TaskPlan, Message, Observation
import logging
from datetime import datetime
import os
import json
import pandas as pd

logger = logging.getLogger(__name__)

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
        settings = state.get("settings", {})  # 获取设置参数
        base_url = settings.get('baseUrl')  # 从设置中获取基础URL

        # 获取历史规划记录（转换为字典格式供增强规划器使用）
        plan_history = state.get("plan_history", [])
        plan_history_dicts = []
        for plan in plan_history:
            if hasattr(plan, 'model_dump'):
                plan_history_dicts.append(plan.model_dump())
            elif hasattr(plan, 'dict'):
                plan_history_dicts.append(plan.dict())
            elif isinstance(plan, dict):
                plan_history_dicts.append(plan)
            else:
                # 如果是其他格式，尝试转换
                plan_dict = {}
                if hasattr(plan, '__dict__'):
                    plan_dict = plan.__dict__.copy()
                plan_history_dicts.append(plan_dict)

        # 从settings获取模型名称
        model_name = settings.get('modelName')
        
        logger.info(f"任务规划 - 用户请求: {user_request[:50]}..." if len(user_request) > 50 else f"任务规划 - 用户请求: {user_request}")
        logger.info(f"任务规划 - 文件内容长度: {len(file_content) if file_content else 0}")
        logger.info(f"任务规划 - 基础URL: {base_url if base_url else '使用默认值'}")
        logger.info(f"任务规划 - 模型名称: {model_name if model_name else '使用默认值'}")
        logger.info(f"任务规划 - 历史规划数量: {len(plan_history_dicts)}")

        # 调用增强的任务规划函数，传入历史规划记录和settings
        task_plan_dict = plan_analysis_task(user_request, file_content, api_key, plan_history_dicts, settings)

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


def replan_analysis_task_node(state: AnalysisState) -> AnalysisState:
    """
    改进的重规划节点
    使用缓存和历史学习来减少不必要的重规划周期
    """
    from llm_services.enhanced_analysis_planner import plan_analysis_task

    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始重规划节点处理")
    logger.info(f"重规划 - 当前迭代: {state.get('iteration_count', 0) + 1}")

    try:
        user_request = state["user_message"]
        file_content = state["file_content"]
        api_key = state["api_key"]
        observation = state.get("observation")
        settings = state.get("settings", {})  # 获取设置参数
        base_url = settings.get('baseUrl')  # 从设置中获取基础URL

        # 获取当前任务计划和观察结果
        current_task_plan = state.get("task_plan")
        computation_results = state.get("computation_results")

        # 检查质量评分是否已满足要求，如果是则跳过重规划
        quality_threshold = float(os.getenv('QUALITY_THRESHOLD', 0.85))
        if observation and observation.quality_score >= quality_threshold:
            logger.info(f"质量评分 {observation.quality_score} >= {quality_threshold}，满足要求，跳过重规划")
            # 直接返回当前状态，不进行重规划
            iteration_count = state.get("iteration_count", 0) + 1
            return {
                **state,
                "current_step": "replanning_skipped",  # 标记跳过重规划
                "error": None,
                "processed": True,
                "needs_replanning": False,
                "iteration_count": iteration_count
            }

        # 获取历史规划记录（转换为字典格式供增强规划器使用）
        plan_history = state.get("plan_history", [])
        plan_history_dicts = []
        for plan in plan_history:
            if hasattr(plan, 'model_dump'):
                plan_history_dicts.append(plan.model_dump())
            elif hasattr(plan, 'dict'):
                plan_history_dicts.append(plan.dict())
            elif isinstance(plan, dict):
                plan_history_dicts.append(plan)
            else:
                # 如果是其他格式，尝试转换
                plan_dict = {}
                if hasattr(plan, '__dict__'):
                    plan_dict = plan.__dict__.copy()
                plan_history_dicts.append(plan_dict)

        # 从settings获取模型名称
        model_name = settings.get('modelName')
        
        logger.info(f"重规划 - 原始请求: {user_request[:50]}..." if len(user_request) > 50 else f"重规划 - 原始请求: {user_request}")
        logger.info(f"重规划 - 文件内容长度: {len(file_content) if file_content else 0}")
        logger.info(f"重规划 - 基础URL: {base_url if base_url else '使用默认值'}")
        logger.info(f"重规划 - 模型名称: {model_name if model_name else '使用默认值'}")
        logger.info(f"重规划 - 历史规划数量: {len(plan_history_dicts)}")
        if observation:
            logger.info(f"重规划 - 观察质量评分: {observation.quality_score}")
            logger.info(f"重规划 - 观察反馈: {observation.feedback[:50] if observation.feedback else 'N/A'}...")

        # 分析观察结果，确定需要改进的方面
        improvement_areas = _analyze_improvement_areas(observation, computation_results)

        # 构建增强的重规划请求
        enhanced_request = _build_enhanced_request(user_request, improvement_areas)

        # 使用增强的规划器进行重规划，传入历史规划记录和settings
        task_plan_dict = plan_analysis_task(enhanced_request, file_content, api_key, plan_history_dicts, settings)

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
        logger.info(f"[{end_time}] 重规划完成: {task_plan.task_type}, 耗时: {duration:.2f}秒")

        # 更新迭代计数
        iteration_count = state.get("iteration_count", 0) + 1

        return {
            **state,
            "task_plan": task_plan,
            "current_step": "replanning",
            "error": None,
            "processed": True,
            "needs_replanning": False,  # 重规划节点完成后设置为False，由观察评估节点重新判断
            "plan_history": plan_history,
            "iteration_count": iteration_count
        }
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 重规划节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        return {
            **state,
            "error": f"重规划失败: {str(e)}",
            "current_step": "replanning_error",
            "processed": True
        }


def _analyze_improvement_areas(observation, computation_results) -> Dict[str, Any]:
    """
    分析需要改进的领域

    Args:
        observation: 观察结果
        computation_results: 计算结果

    Returns:
        dict: 改进领域分析
    """
    improvement_areas = {
        "quality_issues": [],
        "missing_operations": [],
        "data_insights": []
    }

    if observation:
        # 根据观察结果分析质量不足的方面
        quality_score = observation.quality_score

        # 如果质量分数较低，分析具体问题
        if quality_score < 0.5:
            improvement_areas["quality_issues"].append("结果质量过低，需要更深入的分析")
        elif quality_score < 0.8:
            improvement_areas["quality_issues"].append("结果质量一般，需要补充分析")

        # 分析反馈中的具体问题
        feedback = observation.feedback.lower() if observation.feedback else ""
        if "缺乏" in feedback or "不够" in feedback or "不足" in feedback:
            improvement_areas["quality_issues"].append("分析深度不足")
        if "偏离" in feedback or "无关" in feedback:
            improvement_areas["quality_issues"].append("分析方向偏离用户需求")

    # 分析计算结果，找出可能缺失的操作
    if computation_results:
        results_keys = list(computation_results.keys()) if isinstance(computation_results, dict) else []

        # 检查是否缺少常用的统计操作结果
        common_ops = ["总和", "平均值", "最大值", "最小值", "计数", "标准差"]
        for op in common_ops:
            op_found = False
            for key in results_keys:
                if op in str(key):
                    op_found = True
                    break
            if not op_found:
                improvement_areas["missing_operations"].append(op)

    return improvement_areas


def _build_enhanced_request(original_request: str, improvement_areas: Dict[str, Any]) -> str:
    """
    构建增强的重规划请求

    Args:
        original_request: 原始请求
        improvement_areas: 需要改进的领域

    Returns:
        str: 增强的请求
    """
    enhanced_parts = [original_request]

    # 根据改进领域添加具体指导
    if improvement_areas["quality_issues"]:
        enhanced_parts.append("\n\n请特别注意以下方面以提高分析质量:")
        for issue in improvement_areas["quality_issues"]:
            enhanced_parts.append(f"- {issue}")

    if improvement_areas["missing_operations"]:
        enhanced_parts.append("\n\n请补充以下类型的分析操作:")
        for op in improvement_areas["missing_operations"]:
            enhanced_parts.append(f"- {op}")

    if improvement_areas["data_insights"]:
        enhanced_parts.append("\n\n请关注以下数据洞察:")
        for insight in improvement_areas["data_insights"]:
            enhanced_parts.append(f"- {insight}")

    enhanced_parts.append("\n\n请基于之前的分析结果进行改进，避免重复之前的错误。")

    return "\n".join(enhanced_parts)


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
        if hasattr(task_plan, 'model_dump') and callable(getattr(task_plan, 'model_dump')):
            task_plan_dict = task_plan.model_dump()
        elif hasattr(task_plan, 'dict') and callable(getattr(task_plan, 'dict')):
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
        from pydantic import BaseModel
        class LocalObservation(BaseModel):
            """观察结果定义"""
            results: Dict[str, Any] = {}
            quality_score: float = 0.0
            feedback: str = ""
            success: bool = False
            next_actions: list = []
        observation = LocalObservation(
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
        settings = state.get("settings", {})  # 获取设置参数
        base_url = settings.get('baseUrl')  # 从设置中获取基础URL
        model_name = settings.get('modelName')  # 从设置中获取模型名称

        logger.info(f"报告生成 - 任务类型: {task_plan.task_type if task_plan else 'N/A'}")
        logger.info(f"报告生成 - 计算结果项数: {len(computation_results) if computation_results else 0}")
        logger.info(f"报告生成 - 输出表格模式: {output_as_table}")
        logger.info(f"报告生成 - 基础URL: {base_url if base_url else '使用默认值'}")
        logger.info(f"报告生成 - 模型名称: {model_name if model_name else '使用默认值'}")

        # 将TaskPlan转换为字典格式
        task_plan_dict = {
            "task_type": task_plan.task_type,
            "columns": task_plan.columns,
            "operations": task_plan.operations,
            "expected_output": task_plan.expected_output
        }

        # 调用现有的报告生成函数，传递settings参数
        final_report = generate_report(task_plan_dict, computation_results, api_key, output_as_table, base_url, model_name, settings)

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


def chat_node(state: AnalysisState) -> AnalysisState:
    """
    聊天节点
    处理普通聊天请求（非分步分析）
    """
    from llm_services.qwen_engine import chat_with_llm_stream

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

        # 准备模型参数，使用获取到的聊天历史
        model_params = {
            'model': settings.get('modelName', 'qwen-max'),
            'temperature': settings.get('temperature', 0.7),  # 聊天使用用户设置的温度
            'max_tokens': settings.get('maxTokens', 2048),  # 使用用户配置的值，但确保足够大
            'top_p': settings.get('topP', 0.9),
            'frequency_penalty': settings.get('frequencyPenalty', 0.5),
            'api_key': settings.get('apiKey'),  # 只使用settings中的api_key参数
            'base_url': settings.get('baseUrl', None),  # 使用settings中的baseUrl
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
            "final_report": full_response,
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