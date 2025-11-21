"""
LangGraph节点处理器
用于AI数据透视助手的各个节点处理函数
"""
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd
import json
import logging
from datetime import datetime
from .analysis_graph import AnalysisState, TaskPlan, Observation


logger = logging.getLogger(__name__)


def plan_analysis_task_node(state: AnalysisState) -> AnalysisState:
    """
    任务规划节点
    将用户的数据分析请求转换为具体的计算任务
    """
    from llm_services.analysis_planner import plan_analysis_task
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始任务规划节点处理")
    
    try:
        user_request = state["user_message"]
        file_content = state["file_content"]
        api_key = state["api_key"]
        
        logger.info(f"任务规划 - 用户请求: {user_request[:50]}..." if len(user_request) > 50 else f"任务规划 - 用户请求: {user_request}")
        logger.info(f"任务规划 - 文件内容长度: {len(file_content) if file_content else 0}")
        
        # 调用原有的任务规划函数
        task_plan_dict = plan_analysis_task(user_request, file_content, api_key)
        
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
    重新规划节点
    基于观察结果重新规划分析任务
    """
    from llm_services.analysis_planner import plan_analysis_task
    
    start_time = datetime.now()
    logger.info(f"[{start_time}] 开始重新规划节点处理")
    
    try:
        user_request = state["user_message"]
        file_content = state["file_content"]
        api_key = state["api_key"]
        observation = state.get("observation")
        
        logger.info(f"重新规划 - 用户请求: {user_request[:50]}..." if len(user_request) > 50 else f"重新规划 - 用户请求: {user_request}")
        logger.info(f"重新规划 - 基于观察结果: {observation.feedback if observation else '无观察结果'}")
        
        # 构建更详细的请求上下文，包含观察结果
        context_request = f"{user_request}\n\n根据之前的分析结果和反馈：{observation.feedback if observation else '无反馈信息'}\n\n请基于以上信息重新规划分析任务。"
        
        # 调用任务规划函数
        task_plan_dict = plan_analysis_task(context_request, file_content, api_key)
        
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
        logger.info(f"[{end_time}] 重新规划完成: {task_plan.task_type}, 耗时: {duration:.2f}秒")
        logger.info(f"重新规划节点 - 新迭代计数: {state.get('iteration_count', 0) + 1}")
        
        return {
                **state,
                "task_plan": task_plan,
                "current_step": "replanning",
                "error": None,
                "processed": True,
                "needs_replanning": False,
                "plan_history": plan_history,
                "iteration_count": state.get("iteration_count", 0) + 1  # 增加迭代计数
            }
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"[{end_time}] 重新规划节点出错，耗时: {duration:.2f}秒, 错误: {str(e)}")
        return {
            **state,
            "error": f"重新规划失败: {str(e)}",
            "current_step": "replanning_error",
            "processed": True
        }


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


def chat_node(state: 'ChatState') -> 'ChatState':
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