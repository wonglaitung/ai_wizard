"""
观察与评估器模块
用于评估数据分析结果的质量并决定是否需要重新规划
"""

from .qwen_engine import chat_with_llm
import json
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel


class Observation(BaseModel):
    """观察结果定义"""
    results: Dict[str, Any] = {}
    quality_score: float = 0.0
    feedback: str = ""
    success: bool = False
    next_actions: list = []


def evaluate_analysis_results(task_plan: Dict[str, Any], 
                             computation_results: Dict[str, Any], 
                             user_message: str, 
                             api_key: Optional[str] = None,
                             settings: Optional[Dict[str, Any]] = None) -> Observation:
    """
    评估数据分析结果的质量并决定是否需要重新规划
    
    Args:
        task_plan: 任务计划
        computation_results: 计算结果
        user_message: 用户原始请求
        api_key: API密钥
        settings: 模型设置
        
    Returns:
        Observation: 观察结果对象
    """
    # 准备评估提示
    evaluation_prompt = f"""
    请从商业价值和业务洞察角度深入评估以下数据分析结果的质量：

    用户原始请求: {user_message}

    执行的分析计划:
    - 分析类型: {task_plan.get('task_type', '未知任务')}
    - 执行的操作: {task_plan.get('operations', [])}
    - 期望的业务洞察: {task_plan.get('expected_output', '无预期输出')}

    实际分析结果:
    {json.dumps(computation_results, ensure_ascii=False, indent=2)}

    请从以下维度进行评估：

    1. **业务洞察质量** - 分析是否揭示了有价值的业务模式、趋势或异常
    2. **用户需求满足度** - 结果是否直接回答了用户的核心业务问题
    3. **数据完整性** - 分析是否全面覆盖了相关维度和指标
    4. **实际应用价值** - 结果是否支持业务决策和行动

    评估标准：
    - 高质量 (0.9-1.0): 深刻洞察、高度相关、直接支持决策
    - 中高质量 (0.7-0.89): 有价值洞察、基本满足需求、有一定决策支持
    - 中等质量 (0.5-0.69): 基本分析完成、部分满足需求、洞察有限
    - 低质量 (0.0-0.49): 分析浅显、偏离需求、缺乏洞察

    请严格按照以下JSON格式输出：
    {{
      "quality_score": 0.8,
      "meets_requirements": true,
      "feedback": "详细反馈，包括业务发现、分析优点、不足之处",
      "success": true,
      "next_actions": ["具体改进建议或下一步操作"]
    }}
    """
    
    # 准备模型参数
    if settings is None:
        settings = {}
    
    model_params = {
        'model': settings.get('modelName', 'qwen-max'),
        'temperature': 0.1,  # 评估时使用较低的温度以获得更一致的结果
        'max_tokens': 1024,
        'top_p': 0.9,
        'frequency_penalty': 0.5,
        'api_key': api_key,
        'base_url': settings.get('baseUrl', None),
    }
    
    try:
        # 调用LLM进行评估
        evaluation_result_str = chat_with_llm(evaluation_prompt, **model_params)
        
        # 解析评估结果
        # 尝试从响应中提取JSON
        json_match = re.search(r'\{.*\}', evaluation_result_str, re.DOTALL)
        if json_match:
            evaluation_json = json_match.group(0)
            evaluation_data = json.loads(evaluation_json)
            
            # 创建观察结果对象
            observation = Observation(
                results=computation_results,
                quality_score=evaluation_data.get("quality_score", 0.5),
                feedback=evaluation_data.get("feedback", "未提供反馈"),
                success=evaluation_data.get("success", False),
                next_actions=evaluation_data.get("next_actions", [])
            )
            
            return observation
        else:
            # 如果无法解析JSON，返回默认观察结果
            return Observation(
                results=computation_results,
                quality_score=0.5,
                feedback="无法解析评估结果",
                success=False,
                next_actions=[]
            )
            
    except Exception as e:
        # 如果评估出错，返回错误观察结果
        return Observation(
            results=computation_results,
            quality_score=0.0,
            feedback=f"评估过程中发生错误: {str(e)}",
            success=False,
            next_actions=["重新规划分析任务"]
        )


def should_replan_analysis(observation: Observation, quality_threshold: float = 0.7) -> bool:
    """
    根据观察结果决定是否需要重新规划
    
    Args:
        observation: 观察结果
        quality_threshold: 质量阈值，低于此值需要重新规划
        
    Returns:
        bool: 是否需要重新规划
    """
    # 如果质量评分低于阈值，或者未满足需求，则需要重新规划
    needs_replanning = (
        observation.quality_score < quality_threshold or 
        not observation.success or
        len(observation.next_actions) > 0
    )
    
    return needs_replanning