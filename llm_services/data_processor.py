# -*- coding: utf-8 -*-
"""
数据处理器模块
用于执行从商业角度透视数据的具体计算任务
完全依赖大模型在线生成代码
"""

import pandas as pd
import numpy as np
from io import StringIO
import logging
from typing import Dict, Any, Optional
from llm_services.qwen_engine import chat_with_llm

# 配置日志
logger = logging.getLogger(__name__)

def execute_generated_code(code: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    直接执行大模型生成的代码
    """
    try:
        # 清理生成的代码，移除注释和import语句
        cleaned_code = _clean_generated_code(code)
        
        # 创建执行环境
        execution_env = {
            'pd': pd,
            'np': np,
            'df': df
        }
        
        # 检查代码是否包含赋值语句
        if '=' in cleaned_code.strip():
            # 对于赋值语句，使用exec执行
            exec(cleaned_code.strip(), execution_env)
            # 返回最后一个变量的值
            lines = cleaned_code.strip().split('\n')
            last_line = lines[-1].strip()
            if '=' in last_line:
                var_name = last_line.split('=')[0].strip()
                result = execution_env.get(var_name)
            else:
                result = execution_env.get('result')
        else:
            # 对于表达式，使用eval执行
            result = eval(cleaned_code.strip(), execution_env)
        
        return {"result": result, "success": True}
            
    except Exception as e:
        logger.error(f"执行生成的代码时出错: {str(e)}")
        return {"error": str(e), "success": False}


def _clean_generated_code(code: str) -> str:
    """
    清理大模型生成的代码，移除注释和import语句
    """
    # 检查是否包含代码块标记，并提取纯代码
    cleaned_code = code.strip()
    
    # 处理代码块标记
    if '```python' in cleaned_code:
        start_idx = cleaned_code.find('```python') + len('```python')
        end_idx = cleaned_code.find('```', start_idx)
        if end_idx == -1:
            end_idx = len(cleaned_code)
        cleaned_code = cleaned_code[start_idx:end_idx].strip()
    elif '```' in cleaned_code:
        # 找到第一个```之后的内容
        parts = cleaned_code.split('```')
        if len(parts) >= 2:
            # 取第一个代码块的内容
            try:
                cleaned_code = parts[1].strip()
                # 如果还有更多部分，确保只取到下一个```之前的内容
                if len(parts) > 2:
                    next_backtick_idx = cleaned_code.find('```')
                    if next_backtick_idx != -1:
                        cleaned_code = cleaned_code[:next_backtick_idx].strip()
            except:
                # 如果提取失败，使用原始清理逻辑
                pass
    
    # 按行分割代码
    lines = cleaned_code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # 移除行首和行尾的空白
        line = line.strip()
        
        # 跳过空行和注释行
        if not line or line.startswith('#'):
            continue
            
        # 跳过import语句
        if line.startswith('import ') or line.startswith('from '):
            continue
            
        # 如果行中包含注释（#），只保留#之前的部分
        if '#' in line:
            line = line.split('#')[0].rstrip()
            # 如果#前面没有有效代码，跳过整行
            if not line.strip():
                continue
        
        cleaned_lines.append(line)
    
    # 重新组合代码
    cleaned_code = '\n'.join(cleaned_lines)
    return cleaned_code.strip()


def parse_multi_sheet_data(text_data):
    """
    解析包含多工作表的文本数据
    
    Args:
        text_data (str): 包含多工作表标记的文本数据
        
    Returns:
        dict: 工作表名称到DataFrame的映射
    """
    lines = text_data.strip().split('\n')
    current_sheet_name = None
    sheet_data = []
    parsed_dataframes = {}
    
    for line in lines:
        if line.startswith('工作表: ') or line.startswith('Sheet: '):
            # 如果之前有数据，保存之前的表格
            if current_sheet_name and sheet_data:
                try:
                    # 将数据转换为DataFrame
                    df_str = '\n'.join(sheet_data)
                    # 检查数据中是否包含管道符，优先使用管道符分隔
                    if '|' in df_str:
                        df = pd.read_csv(StringIO(df_str), sep='|')
                    else:
                        df = pd.read_csv(StringIO(df_str))
                    parsed_dataframes[current_sheet_name] = df
                except Exception as e:
                    logger.error(f"无法解析工作表 {current_sheet_name} 的数据: {str(e)}")
                        
            # 开始新工作表
            if line.startswith('工作表: '):
                current_sheet_name = line.split('工作表: ')[1].strip()
            elif line.startswith('Sheet: '):
                current_sheet_name = line.split('Sheet: ')[1].strip()
            sheet_data = []
        else:
            # 如果不是空行，添加到当前工作表数据
            if line.strip():
                sheet_data.append(line)
    
    # 处理最后一个工作表的数据
    if current_sheet_name and sheet_data:
        try:
            df_str = '\n'.join(sheet_data)
            if '|' in df_str:
                df = pd.read_csv(StringIO(df_str), sep='|')
            else:
                df = pd.read_csv(StringIO(df_str))
            parsed_dataframes[current_sheet_name] = df
        except:
            logger.error(f"无法解析工作表 {current_sheet_name} 的数据")
    
    return parsed_dataframes


def process_data(task_plan, file_content=None, api_key=None, settings=None):
    """
    根據任務計劃執行數據處理，從商業角度透視數據
    完全依賴大模型在線生成代碼
    
    Args:
        task_plan (dict): 任務計劃
        file_content (str): 文件內容
        api_key (str): API密鑰，用於大模型調用
        settings (dict): 模型設置參數
        
    Returns:
        dict: 計算結果
    """
    # 解析数据
    df = pd.DataFrame()
    multi_sheet_data = None
    
    if file_content:
        # 檢查是否是多工作表數據
        if "工作表: " in file_content or "Sheet: " in file_content:
            multi_sheet_data = parse_multi_sheet_data(file_content)
            # 如果有多工作表，根据任务计划的需要进行处理
            if multi_sheet_data:
                # 如果任务计划明确涉及到多个工作表的列，我们需要处理这些工作表
                task_columns = task_plan.get("columns", [])
                
                # 检查任务计划中是否涉及多个工作表中的不同列
                has_cross_sheet_analysis = any("_月末" in col for col in task_columns) or \
                                          any("Sheet" in col for col in task_columns) or \
                                          len([col for col in task_columns if "客户编码清单" in col]) > 1
                                          
                if has_cross_sheet_analysis:
                    # 如果需要跨工作表分析，使用专门的处理函数
                    df = _handle_cross_sheet_operations(multi_sheet_data, task_plan, api_key, settings)
                else:
                    # 如果不需要跨工作表分析，使用第一个工作表
                    df = list(multi_sheet_data.values())[0]
            else:
                df = pd.DataFrame()
        else:
            # 解析单工作表数据
            try:
                df = pd.read_csv(StringIO(file_content))
            except:
                df = pd.DataFrame()

    results = {}
    
    # 获取操作列表
    operations = task_plan.get("operations", [])
    
    for op in operations:
        try:
            op_name = op.get("name")
            
            # 为每个操作更新数据列信息
            current_df = df
            # 如果操作涉及到特定的跨工作表列，我们需要动态处理
            op_column = op.get("column", "")
            if isinstance(op_column, list) and any("_月末" in col or "Sheet" in col for col in op_column):
                # 这是跨工作表操作，需要特殊处理
                if multi_sheet_data and len(multi_sheet_data) >= 2:
                    # 重新构建DataFrame以包含所有工作表的列
                    sheet_names = list(multi_sheet_data.keys())
                    if len(sheet_names) >= 2:
                        first_sheet_name = sheet_names[0]
                        second_sheet_name = sheet_names[1]
                        
                        # 创建一个包含所有列的DataFrame
                        first_df = multi_sheet_data[first_sheet_name].copy()
                        second_df = multi_sheet_data[second_sheet_name].copy()
                        
                        # 重命名列以区分不同工作表
                        first_customer_col = [col for col in first_df.columns if "客户编码" in col]
                        second_customer_col = [col for col in second_df.columns if "客户编码" in col]
                        first_team_col = [col for col in first_df.columns if "团队" in col]
                        second_team_col = [col for col in second_df.columns if "团队" in col]
                        
                        if first_customer_col and second_customer_col:
                            first_customer_col = first_customer_col[0]
                            second_customer_col = second_customer_col[0]
                            
                            # 重命名列
                            first_rename_dict = {first_customer_col: f"{first_sheet_name}_{first_customer_col}"}
                            if first_team_col:
                                first_rename_dict[first_team_col[0]] = f"{first_sheet_name}_{first_team_col[0]}"
                            
                            second_rename_dict = {second_customer_col: f"{second_sheet_name}_{second_customer_col}"}
                            if second_team_col:
                                second_rename_dict[second_team_col[0]] = f"{second_sheet_name}_{second_team_col[0]}"
                            
                            first_df_renamed = first_df.rename(columns=first_rename_dict)
                            second_df_renamed = second_df.rename(columns=second_rename_dict)
                            
                            # 尝试合并两个DataFrame（如果它们有可合并的结构）
                            # 如果没有共同的列（如客户ID），则无法直接合并，需要特殊处理
                            if first_team_col and second_team_col:
                                # 创建一个客户对比DataFrame
                                first_customers = first_df_renamed[f"{first_sheet_name}_{first_customer_col}"].dropna()
                                second_customers = second_df_renamed[f"{second_sheet_name}_{second_customer_col}"].dropna()
                                
                                # 为每个客户添加期初和期末信息
                                first_df_renamed['_period'] = first_sheet_name
                                second_df_renamed['_period'] = second_sheet_name
                                
                                current_df = pd.concat([first_df_renamed, second_df_renamed], ignore_index=True)
                            else:
                                # 如果没有团队列，也尝试合并
                                first_df_renamed['_period'] = first_sheet_name
                                second_df_renamed['_period'] = second_sheet_name
                                current_df = pd.concat([first_df_renamed, second_df_renamed], ignore_index=True)
            
            # 使用大模型生成代码来执行操作
            user_request = f"""
            你是一个pandas专家，基于以下任务计划和数据，生成对应的pandas代码：
            
            操作: {op}
            数据列: {list(current_df.columns)}
            
            请生成直接可用的pandas代码，用于执行该操作。
            代码应该只包含计算逻辑，不要包含函数定义。
            可用的变量是df（DataFrame）。
            """
            
            model_params = {
                'model': settings.get('modelName', 'qwen-max') if settings else 'qwen-max',
                'temperature': 0.1,
                'max_tokens': 1024,
                'top_p': 0.8,
                'frequency_penalty': 0.5,
                'api_key': api_key,
                'base_url': settings.get('baseUrl', None) if settings else None,
            }
            
            # 生成代码
            generated_code = chat_with_llm(user_request, **model_params)
            
            # 清理并执行生成的代码
            execution_result = execute_generated_code(generated_code, current_df)
            
            if execution_result["success"]:
                results[f"{op_name}_result"] = _convert_pandas_types(execution_result["result"])
            else:
                results[f"{op_name}_error"] = f"代码执行错误: {execution_result['error']}"
                
        except Exception as e:
            results[op.get("name", "unknown")] = f"处理错误: {str(e)}"
    
    return results


def _handle_cross_sheet_operations(multi_sheet_data, task_plan, api_key, settings):
    """
    处理跨工作表操作，如客户留存分析等
    """
    # 创建一个DataFrame来存储跨工作表分析结果
    # 这里我们假设工作表的结构相似，例如都是包含客户编码和团队信息的表
    
    if len(multi_sheet_data) < 2:
        # 如果只有一个工作表，返回该工作表的数据
        return list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()
    
    # 获取工作表名称列表
    sheet_names = list(multi_sheet_data.keys())
    
    # 假设我们要比较第一个和第二个工作表（如1月末和2月末）
    if len(sheet_names) >= 2:
        first_sheet_name = sheet_names[0]
        second_sheet_name = sheet_names[1]
        
        first_df = multi_sheet_data[first_sheet_name].copy()
        second_df = multi_sheet_data[second_sheet_name].copy()
        
        # 获取客户编码列的名称
        first_customer_col = [col for col in first_df.columns if "客户编码" in col or "编码" in col]
        second_customer_col = [col for col in second_df.columns if "客户编码" in col or "编码" in col]
        
        if first_customer_col and second_customer_col:
            first_customer_col = first_customer_col[0]
            second_customer_col = second_customer_col[0]
            
            # 获取团队列的名称
            first_team_col = [col for col in first_df.columns if "团队" in col]
            second_team_col = [col for col in second_df.columns if "团队" in col]
            
            first_team_col = first_team_col[0] if first_team_col else None
            second_team_col = second_team_col[0] if second_team_col else None
            
            # 为每个DataFrame添加工作表标识
            first_df = first_df.rename(columns={first_customer_col: f"{first_sheet_name}_{first_customer_col}",
                                                first_team_col: f"{first_sheet_name}_{first_team_col}"}) if first_team_col else first_df.rename(columns={first_customer_col: f"{first_sheet_name}_{first_customer_col}"})
            second_df = second_df.rename(columns={second_customer_col: f"{second_sheet_name}_{second_customer_col}",
                                                  second_team_col: f"{second_sheet_name}_{second_team_col}"}) if second_team_col else second_df.rename(columns={second_customer_col: f"{second_sheet_name}_{second_customer_col}"})
            
            # 重命名后重新获取列名
            first_customer_col_renamed = f"{first_sheet_name}_{first_customer_col}"
            second_customer_col_renamed = f"{second_sheet_name}_{second_customer_col}"
            first_team_col_renamed = f"{first_sheet_name}_{first_team_col}" if first_team_col else None
            second_team_col_renamed = f"{second_sheet_name}_{second_team_col}" if second_team_col else None
            
            # 获取两个时间点的客户集合
            first_customers = set(first_df[first_customer_col_renamed].dropna())
            second_customers = set(second_df[second_customer_col_renamed].dropna())
            
            # 计算留存、新增、流失客户
            retained_customers = first_customers & second_customers  # 两个时间点都有的客户
            new_customers = second_customers - first_customers       # 新增客户
            lost_customers = first_customers - second_customers      # 流失客户
            
            # 创建留存分析结果DataFrame
            retention_data = {
                'retained_customers_count': [len(retained_customers)],
                'new_customers_count': [len(new_customers)],
                'lost_customers_count': [len(lost_customers)],
                'first_period_total': [len(first_customers)],
                'second_period_total': [len(second_customers)],
                'retention_rate': [len(retained_customers) / len(first_customers) if len(first_customers) > 0 else 0]
            }
            
            # 创建一个包含留存分析结果的DataFrame
            result_df = pd.DataFrame(retention_data)
            
            # 添加原始数据的统计信息
            if first_team_col_renamed and second_team_col_renamed:
                # 按团队统计各时间点的客户数量
                first_team_counts = first_df[first_team_col_renamed].value_counts() if first_team_col else pd.Series([], dtype=object)
                second_team_counts = second_df[second_team_col_renamed].value_counts() if second_team_col else pd.Series([], dtype=object)
                
                # 合并统计结果
                if not first_team_counts.empty and not second_team_counts.empty:
                    team_comparison = pd.DataFrame({
                        f'{first_sheet_name}_count': first_team_counts,
                        f'{second_sheet_name}_count': second_team_counts
                    }).fillna(0)
                    
                    # 将团队比较数据添加到结果中
                    for team in team_comparison.index:
                        result_df[f'{team}_change'] = team_comparison.loc[team, f'{second_sheet_name}_count'] - \
                                                      team_comparison.loc[team, f'{first_sheet_name}_count']
                elif not first_team_counts.empty:
                    team_comparison = pd.DataFrame({
                        f'{first_sheet_name}_count': first_team_counts
                    })
                    for team in team_comparison.index:
                        result_df[f'{team}_change'] = -team_comparison.loc[team, f'{first_sheet_name}_count']
                elif not second_team_counts.empty:
                    team_comparison = pd.DataFrame({
                        f'{second_sheet_name}_count': second_team_counts
                    })
                    for team in team_comparison.index:
                        result_df[f'{team}_change'] = team_comparison.loc[team, f'{second_sheet_name}_count']
            
            # 同时创建一个合并的DataFrame，其中包含所有跨工作表的信息
            # 为每个DataFrame添加工作表标签
            first_df_with_label = first_df.copy()
            first_df_with_label['_period'] = first_sheet_name
            second_df_with_label = second_df.copy()
            second_df_with_label['_period'] = second_sheet_name
            
            # 合并两个数据框
            combined_df = pd.concat([first_df_with_label, second_df_with_label], ignore_index=True)
            
            # 添加留存分析结果到合并的DataFrame
            for col, val in retention_data.items():
                combined_df[col] = val[0] if isinstance(val, list) else val
            
            return combined_df
        else:
            # 如果没有找到客户编码列，返回第一个工作表的数据
            return first_df
    else:
        # 如果没有多个工作表，返回第一个工作表的数据
        return list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()


def _convert_pandas_types(obj):
    """
    将pandas和numpy数据类型转换为Python原生类型以支持JSON序列化
    """
    # 首先检查是否是pandas或numpy对象，避免触发布尔判断错误
    if isinstance(obj, pd.Series):
        # Series对象的特殊处理
        try:
            return _convert_pandas_types(obj.to_dict())
        except:
            try:
                # 确保索引被转换为字符串作为字典的键
                return {str(idx): _convert_pandas_types(val) for idx, val in obj.items()}
            except:
                try:
                    return _convert_pandas_types(obj.tolist())
                except:
                    return str(obj)
    elif isinstance(obj, pd.DataFrame):
        # DataFrame对象的特殊处理
        try:
            return _convert_pandas_types(obj.to_dict())
        except:
            try:
                return _convert_pandas_types(obj.to_dict(orient='records'))
            except:
                return str(obj)
    elif isinstance(obj, np.ndarray):
        # numpy数组的特殊处理
        try:
            return _convert_pandas_types(obj.tolist())
        except:
            return str(obj)
    elif hasattr(obj, 'agg') or str(type(obj)).endswith("GroupBy'>"):
        # GroupBy对象的特殊处理
        try:
            if hasattr(obj, 'sum'):
                df_result = obj.sum()
                return _convert_pandas_types(df_result)
        except:
            try:
                if hasattr(obj, 'mean'):
                    df_result = obj.mean()
                    return _convert_pandas_types(df_result)
            except:
                try:
                    if hasattr(obj, 'first'):
                        df_result = obj.first()
                        return _convert_pandas_types(df_result)
                except:
                    return f"GroupBy object: {str(obj)[:100]}..."
        return f"GroupBy object: {str(obj)[:100]}..."
    elif isinstance(obj, dict):
        # 确保字典的键是可序列化的类型
        result = {}
        for key, value in obj.items():
            # 将键转换为字符串以确保可序列化
            safe_key = str(key) if not isinstance(key, (str, int, float, bool)) else key
            result[safe_key] = _convert_pandas_types(value)
        return result
    elif isinstance(obj, list):
        return [_convert_pandas_types(item) for item in obj]
    elif isinstance(obj, tuple):
        # 将tuple转换为list，因为JSON不支持tuple
        return [_convert_pandas_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    else:
        return obj
