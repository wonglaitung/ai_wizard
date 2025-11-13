# -*- coding: utf-8 -*-
"""
分析任务规划器模块
用于将用户的数据分析请求转换为具体的计算任务
"""

import json
from .qwen_engine import chat_with_llm
from .data_processor import OPERATION_REGISTRY

def plan_analysis_task(user_request, file_content=None, api_key=None):
    """
    使用大模型规划数据分析任务
    
    Args:
        user_request (str): 用户的分析请求
        file_content (str): 上传的文件内容（可选）
        api_key (str): API密钥
        
    Returns:
        dict: 包含分析任务的详细信息
    """
    
    # 如果没有提供api_key，从环境变量获取
    import os
    if api_key is None:
        api_key = os.getenv('QWEN_API_KEY', '')
        if not api_key:
            api_key = os.getenv('DASHSCOPE_API_KEY', '')
    
    # 获取支持的操作列表
    supported_operations = list(OPERATION_REGISTRY.keys())
    
    # 为规划器提供操作的详细说明
    operation_descriptions = {
        "mean": "计算数值列的平均值",
        "sum": "计算数值列的总和",
        "max": "找出数值列的最大值",
        "min": "找出数值列的最小值",
        "count": "计算列中非空值的数量",
        "percentage": "计算每个唯一值的百分比",
        "std": "计算数值列的标准差",
        "unique": "获取列中的唯一值",
        "median": "计算数值列的中位数",
        "mode": "计算列的众数（出现频率最高的值）",
        "variance": "计算数值列的方差",
        "quantile_25": "计算数值列的25%分位数",
        "quantile_75": "计算数值列的75%分位数",
        "range": "计算数值列的范围（最大值-最小值）",
        "first": "获取列中的第一行数据",
        "last": "获取列中的最后一行数据",
        "missing_count": "计算列中缺失值的数量",
        "missing_percentage": "计算列中缺失值的百分比",
        "correlation": "计算数值列之间的相关性矩阵"
    }
    
    # 构建操作说明字符串
    operations_info = "\n".join([f"{op}: {operation_descriptions.get(op, '执行基本统计操作')}" for op in supported_operations])
    
    # 构建提示词
    prompt = f"""
你是一个数据分析任务规划专家。请将用户的请求转换为具体的计算任务。

用户请求: {user_request}

文件内容:
{file_content if file_content else "无文件内容"}

系统支持以下操作:
{operations_info}

请按照以下格式输出JSON响应，包含以下字段：
1. "task_type": 任务类型（如：统计分析、趋势分析、相关性分析等）
2. "columns": 需要分析的列名列表
3. "operations": 需要执行的操作列表，操作名称必须从系统支持的操作中选择
4. "expected_output": 预期的输出结果描述

示例输出格式：
{{
    "task_type": "描述性统计分析",
    "columns": ["销售额", "日期"],
    "operations": [
        {{"name": "mean", "column": "销售额", "description": "计算销售额的平均值"}},
        {{"name": "max", "column": "销售额", "description": "找出销售额的最大值"}},
        {{"name": "min", "column": "销售额", "description": "找出销售额的最小值"}}
    ],
    "expected_output": "输出销售额的平均值、最大值和最小值"
}}

请严格按照上述JSON格式输出，不要包含其他内容。
"""
    
    try:
        # 调用大模型获取任务规划
        response = chat_with_llm(prompt, model="qwen-max", temperature=0.3, api_key=api_key)
        
        # 解析JSON响应
        task_plan = json.loads(response)
        return task_plan
    except Exception as e:
        # 如果解析失败，返回默认任务计划
        return {
            "task_type": "基础分析",
            "columns": [],
            "operations": [],
            "expected_output": "执行基础数据分析",
            "error": str(e)
        }