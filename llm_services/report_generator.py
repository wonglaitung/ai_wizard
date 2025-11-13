# -*- coding: utf-8 -*-
"""
报告生成器模块
用于整合计算结果并生成最终分析报告
"""

from .qwen_engine import chat_with_llm

def generate_report(task_plan, computation_results, api_key=None):
    """
    生成数据分析报告
    
    Args:
        task_plan (dict): 原始任务计划
        computation_results (dict): 计算结果
        api_key (str): API密钥
        
    Returns:
        str: 生成的分析报告
    """
    
    # 如果没有提供api_key，从环境变量获取
    import os
    if api_key is None:
        api_key = os.getenv('QWEN_API_KEY', '')
    
    if not api_key:
        return "生成报告时出错: 未提供API密钥"
    
    # 构建提示词
    prompt = f"""
你是一个专业的数据分析师，负责根据计算结果生成详细的分析报告。

任务类型: {task_plan.get('task_type', '未知任务')}
预期输出: {task_plan.get('expected_output', '无预期输出')}

计算结果:
{computation_results}

请根据以上计算结果，生成一份详细的分析报告，包括：
1. 对计算结果的解释
2. 数据中的关键发现
3. 可能的趋势或模式
4. 相关建议

请确保报告内容准确、专业且易于理解。
"""
    
    try:
        # 调用大模型生成报告
        report = chat_with_llm(prompt, model="qwen-max", temperature=0.5, api_key=api_key)
        return report
    except Exception as e:
        return f"生成报告时出错: {str(e)}"