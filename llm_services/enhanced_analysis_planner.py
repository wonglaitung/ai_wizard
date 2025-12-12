"""
改进的分析任务规划器模块
移除缓存机制，简化智能初始规划系统
"""

import json
from typing import Dict, Any, List, Optional
from .qwen_engine import chat_with_llm
import logging
import os
import re

logger = logging.getLogger(__name__)

class EnhancedAnalysisPlanner:
    """
    增强的分析规划器，移除缓存机制
    """
    
    def __init__(self):
        pass
        self.operation_descriptions = {
            "mean": "计算数值列的平均值",
            "sum": "计算数值列的总和",
            "max": "找出数值列的最大值",
            "min": "找出数值列的最小值",
            "percentage": "计算每个唯一值的百分比",
            "mode": "计算列的众数（出现频率最高的值）",
            "range": "计算数值列的范围（最大值-最小值）",
            "correlation": "计算数值列之间的相关性矩阵",
            "group_by": "按指定列分组并计算聚合统计（如sum、mean、count、max、min等）",
            "cross_tab": "创建交叉表分析两个分类变量之间的关系",
            "pivot_table": "创建透视表，按行和列进行交叉汇总",
            "aggregate": "执行复杂的聚合操作，可对指定列应用多种统计函数"
        }
        # 现在支持的操作列表是硬编码的，因为数据处理器完全依赖大模型生成代码
        self.supported_operations = list(self.operation_descriptions.keys())
    
    def plan_analysis_task(self, user_request: str, file_content: str = None, api_key: str = None,
                          plan_history: List[Dict] = None, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        使用大模型规划数据分析任务，移除缓存机制
        
        Args:
            user_request: 用户的分析请求
            file_content: 上传的文件内容（可选）
            api_key: API密钥
            plan_history: 历史规划记录（用于学习和改进）
            settings: 模型设置参数
            
        Returns:
            dict: 包含分析任务的详细信息
        """
        # 直接执行规划，不再使用缓存
        task_plan = self._generate_task_plan(user_request, file_content, api_key, plan_history, settings)
        
        return task_plan
    
    def _generate_task_plan(self, user_request: str, file_content: str = None, api_key: str = None, 
                           plan_history: List[Dict] = None, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成分析任务计划的核心实现
        
        Args:
            user_request: 用户的分析请求
            file_content: 上传的文件内容
            api_key: API密钥
            plan_history: 历史规划记录
            base_url: API基础URL
            
        Returns:
            dict: 分析任务计划
        """
        # 如果没有提供api_key，从环境变量获取
        if api_key is None:
            api_key = os.getenv('QWEN_API_KEY', '')
            if not api_key:
                api_key = os.getenv('DASHSCOPE_API_KEY', '')
        
        # 从settings中获取model_name和base_url
        model_name = settings.get('modelName') if settings else None
        base_url = settings.get('baseUrl') if settings else None
        
        # 获取支持的操作列表
        operations_info = "\n".join([f"{op}: {self.operation_descriptions.get(op, '执行基本统计操作')}" for op in self.supported_operations])
        
        # 历史规划学习提示
        learning_context = ""
        if plan_history:
            learning_context = self._format_learning_context(plan_history)
        
        # 解析文件内容以获取实际列名
        actual_columns = []
        if file_content:
            # 尝试解析多工作表数据
            if "工作表: " in file_content or "Sheet: " in file_content:
                # 解析多工作表数据结构
                from io import StringIO
                lines = file_content.strip().split('\n')
                current_sheet_name = None
                for line in lines:
                    if line.startswith('工作表: ') or line.startswith('Sheet: '):
                        if line.startswith('工作表: '):
                            current_sheet_name = line.split('工作表: ')[1].strip()
                        elif line.startswith('Sheet: '):
                            current_sheet_name = line.split('Sheet: ')[1].strip()
                    elif current_sheet_name and '|' in line and not line.startswith('工作表: ') and not line.startswith('Sheet: '):
                        # 这是数据行，获取列名（第一行通常是列名）
                        columns = [f"{current_sheet_name}_{col.strip()}" for col in line.split('|') if col.strip()]
                        actual_columns.extend(columns)
                        break
            else:
                # 解析单工作表数据
                try:
                    import pandas as pd
                    df = pd.read_csv(StringIO(file_content))
                    actual_columns = df.columns.tolist()
                except:
                    # 如果解析失败，尝试手动解析
                    if file_content:
                        lines = file_content.strip().split('\n')
                        for line in lines:
                            if '|' in line and not line.startswith('工作表: ') and not line.startswith('Sheet: '):
                                actual_columns = [col.strip() for col in line.split('|') if col.strip()]
                                break
        
        # 构建提示词，包含智能初始规划和历史学习
        prompt = f"""你是一个业务数据分析专家。你的任务是将用户的请求转换为具体的计算任务，帮助用户从业务角度透视数据。

用户请求: {user_request}

文件内容:
{file_content if file_content else "无文件内容"}

可用列名: {actual_columns}

历史规划记录（用于学习和改进）:
{learning_context if learning_context else "无历史规划记录"}

系统支持以下操作（用于业务数据透视）:
{operations_info}

注意事项：
不要对无意义的主键（如客户号）进行分析。
金额属于度量值, 应在分析中用于汇总统计，而非做为分组或分类的维度。

IMPORTANT: 请严格按照以下JSON格式输出，仅输出JSON内容：
{{
    "task_type": "任务类型（如：业务指标分析、业务趋势分析、业务构成分析、业务关联分析、业务诊断等）",
    "columns": ["需要分析的列名列表"],
    "operations": [
        {{
            "name": "操作名称",
            "column": "操作针对的列名或列名列表",
            "description": "操作的描述"
        }}
    ],
    "expected_output": "用一句话来从业务角度简单描述预期的输出结果",
    "rationale": "用一句话来简单解释选择这些操作的原因"
}}

示例输出格式：
{{
    "task_type": "数据分析",
    "columns": ["数值列1", "分类列1"],
    "operations": [
        {{"name": "sum", "column": "数值列1", "description": "计算指定列的总和"}},
        {{"name": "mean", "column": "数值列1", "description": "计算指定列的平均值"}},
        {{"name": "max", "column": "数值列1", "description": "找出指定列的最大值"}}
    ],
    "expected_output": "输出指定列的总和、平均值和最大值",
    "rationale": "基于用户请求和数据特征，选择适当的统计操作"
}}
"""
        
        try:
            # 准备模型参数 - 只使用传入的api_key参数
            # 构建settings字典，优先使用传入的参数
            settings = settings or {}
            if model_name:
                settings['modelName'] = model_name
            if base_url:
                settings['baseUrl'] = base_url
            
            from .qwen_engine import create_model_params
            model_params = create_model_params(
                settings=settings,
                api_key=api_key,
                default_model='qwen-max',
                default_temperature=0.3,  # 任务规划使用较低的温度以获得更稳定的结果
                default_max_tokens=2048   # 使用用户配置的值，但确保足够大
            )
            
            # 调用大模型获取任务规划
            response = chat_with_llm(prompt, **model_params)
            
            # 解析JSON响应
            task_plan = json.loads(response)
            
            # 验证返回的计划是否包含必要的字段
            required_fields = ["task_type", "columns", "operations", "expected_output", "rationale"]
            for field in required_fields:
                if field not in task_plan:
                    logger.warning(f"规划中缺少字段: {field}")
                    task_plan[field] = "" if field in ["task_type", "expected_output", "rationale"] else [] if field in ["columns"] else []
            
            return task_plan
        except json.JSONDecodeError as e:
            logger.error(f"分析任务规划JSON解析出错: {str(e)}")
            logger.error(f"原始LLM回复内容: {response}")
            # 如果解析失败，返回默认任务计划
            return {
                "task_type": "基础分析",
                "columns": [],
                "operations": [],
                "expected_output": "执行基础数据分析",
                "rationale": "由于规划出错，使用基础分析任务",
                "error": f"JSON解析错误: {str(e)}"
            }
        except Exception as e:
            logger.error(f"分析任务规划出错: {str(e)}")
            # 如果有response变量，也记录原始回复
            if 'response' in locals():
                logger.error(f"原始LLM回复内容: {response}")
            # 如果解析失败，返回默认任务计划
            return {
                "task_type": "基础分析",
                "columns": [],
                "operations": [],
                "expected_output": "执行基础数据分析",
                "rationale": "由于规划出错，使用基础分析任务",
                "error": str(e)
            }
    
    def _format_learning_context(self, plan_history: List[Dict]) -> str:
        """
        格式化历史规划上下文，用于智能初始规划
        
        Args:
            plan_history: 历史规划记录
            
        Returns:
            str: 格式化的学习上下文
        """
        if not plan_history:
            return "无历史规划记录"
        
        # 只取最近的3次规划历史以减少提示词长度
        recent_history = plan_history[-3:]
        
        formatted_history = ["历史规划记录:"]
        for i, plan in enumerate(recent_history, 1):
            formatted_history.append(f"规划 {i}:")
            formatted_history.append(f"- 任务类型: {plan.get('task_type', 'N/A')}")
            formatted_history.append(f"- 使用操作: {[op.get('name', 'N/A') for op in plan.get('operations', [])]}")
            formatted_history.append(f"- 预期输出: {plan.get('expected_output', 'N/A')}")
            formatted_history.append("")
        
        return "\n".join(formatted_history)


# 创建全局实例
enhanced_planner = EnhancedAnalysisPlanner()


def plan_analysis_task(user_request: str, file_content: str = None, api_key: str = None, 
                      plan_history: List[Dict] = None, settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    使用增强的分析规划器规划数据分析任务
    
    Args:
        user_request: 用户的分析请求
        file_content: 上传的文件内容（可选）
        api_key: API密钥
        plan_history: 历史规划记录
        settings: 模型设置参数
        
    Returns:
        dict: 包含分析任务的详细信息
    """
    return enhanced_planner.plan_analysis_task(user_request, file_content, api_key, plan_history, settings)
