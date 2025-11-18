# -*- coding: utf-8 -*-
"""
报告生成器模块
用于整合计算结果并生成最终分析报告，侧重于业务数据透视和洞察分析
"""

from .qwen_engine import chat_with_llm

def generate_report(task_plan, computation_results, api_key=None):
    """
    生成业务数据透视分析报告
    
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
    
    # 构建提示词，更侧重于业务数据透视和洞察
    prompt = f"""
你是一个专业的业务数据分析师，专门从事数据透视和业务洞察分析。请根据以下信息生成一份专业的业务分析报告。

任务类型: {task_plan.get('task_type', '未知任务')}
预期输出: {task_plan.get('expected_output', '无预期输出')}

计算结果:
{computation_results}

请根据以上计算结果，生成一份专业的业务数据透视分析报告，重点关注：
1. 业务指标表现：从商业角度解释数据含义
2. 关键业务发现：识别重要的业务趋势、模式或异常
3. 业务洞察：基于数据提供深入的业务洞察和见解
4. 业务影响：分析这些发现对业务的影响
5. 行动建议：提供可执行的业务建议和策略
6. 风险与机遇：识别潜在的业务风险和机遇

请确保报告内容从业务角度出发，专业且易于理解，避免过多技术术语，重点突出业务价值和可操作的洞察。
"""
    
    try:
        # 调用大模型生成报告
        report = chat_with_llm(prompt, model="qwen-max", temperature=0.5, api_key=api_key)
        return report
    except Exception as e:
        return f"生成报告时出错: {str(e)}"