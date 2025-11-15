# -*- coding: utf-8 -*-
"""
分析任务规划器模块
用于将用户的数据分析请求转换为具体的计算任务，更注重从业务角度进行数据透视
"""

import json
from .qwen_engine import chat_with_llm
from .data_processor import OPERATION_REGISTRY

def plan_analysis_task(user_request, file_content=None, api_key=None):
    """
    使用大模型规划数据分析任务，从业务角度进行数据透视
    
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
    
    # 为规划器提供操作的详细说明，更注重业务用途
    operation_descriptions = {
        "mean": "计算数值列的平均值，用于了解业务指标的平均水平",
        "sum": "计算数值列的总和，用于了解业务指标的总体规模",
        "max": "找出数值列的最大值，用于识别业务中的峰值表现",
        "min": "找出数值列的最小值，用于识别业务中的最低表现",
        "count": "计算列中非空值的数量，用于了解数据覆盖范围",
        "percentage": "计算每个唯一值的百分比，用于分析业务构成比例",
        "std": "计算数值列的标准差，用于评估业务指标的波动性",
        "unique": "获取列中的唯一值，用于了解业务分类的多样性",
        "median": "计算数值列的中位数，用于了解业务指标的中间水平",
        "mode": "计算列的众数（出现频率最高的值），用于识别最常见的业务情况",
        "variance": "计算数值列的方差，用于评估业务指标的离散程度",
        "quantile_25": "计算数值列的25%分位数，用于了解业务指标的低分段表现",
        "quantile_75": "计算数值列的75%分位数，用于了解业务指标的高分段表现",
        "range": "计算数值列的范围（最大值-最小值），用于了解业务指标的波动区间",
        "first": "获取列中的第一行数据，用于了解业务的起始状态",
        "last": "获取列中的最后一行数据，用于了解业务的最新状态",
        "missing_count": "计算列中缺失值的数量，用于评估数据完整性",
        "missing_percentage": "计算列中缺失值的百分比，用于评估数据质量",
        "correlation": "计算数值列之间的相关性矩阵，用于识别业务指标间的关联性"
    }
    
    # 构建操作说明字符串
    operations_info = "\n".join([f"{op}: {operation_descriptions.get(op, '执行基本统计操作')}" for op in supported_operations])
    
    # 构建提示词，更注重业务角度的数据透视
    prompt = f"""
你是一个业务数据分析专家。你的任务是将用户的请求转换为具体的计算任务，帮助用户从业务角度透视数据。

用户请求: {user_request}

文件内容:
{file_content if file_content else "无文件内容"}

系统支持以下操作（用于业务数据透视）:
{operations_info}

请按照以下格式输出JSON响应，包含以下字段：
1. "task_type": 任务类型（如：业务指标分析、业务趋势分析、业务构成分析、业务关联分析、业务诊断等）
2. "columns": 需要分析的列名列表
3. "operations": 需要执行的操作列表，操作名称必须从系统支持的操作中选择
4. "expected_output": 预期的输出结果描述（从业务角度解释）

示例输出格式：
{{
    "task_type": "业务指标分析",
    "columns": ["销售额", "日期"],
    "operations": [
        {{"name": "sum", "column": "销售额", "description": "计算销售额的总和，了解业务总体规模"}},
        {{"name": "mean", "column": "销售额", "description": "计算销售额的平均值，了解平均水平"}},
        {{"name": "max", "column": "销售额", "description": "找出销售额的最大值，识别最佳表现"}}
    ],
    "expected_output": "输出销售额的总和、平均值和最大值，帮助理解业务规模和最佳表现"
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