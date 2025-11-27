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
        
        # 检查代码是否包含赋值语句（仅检查不在括号内的等号）
        # 这样可以区分真正的赋值语句和函数参数中的等号
        def has_assignment(code_str):
            """检查代码中是否包含赋值语句（不在括号内的等号）"""
            paren_level = 0
            i = 0
            while i < len(code_str):
                char = code_str[i]
                if char == '(':
                    paren_level += 1
                elif char == ')':
                    paren_level -= 1
                elif char == '=' and paren_level == 0:
                    # 检查等号前的字符，确保是真正的赋值
                    # 例如: "result = df.pivot_table(...)" 是赋值
                    # 但 "df.pivot_table(index='col')" 不是赋值
                    j = i - 1
                    while j >= 0 and code_str[j].isspace():
                        j -= 1
                    if j >= 0 and code_str[j] != ')' and code_str[j] != '(':
                        # 检查等号后是否有空格或变量名，这更可能是赋值
                        return True
                i += 1
            return False
        
        if has_assignment(cleaned_code.strip()):
            # 对于赋值语句，使用exec执行
            exec(cleaned_code.strip(), execution_env)
            # 返回最后一个变量的值
            lines = cleaned_code.strip().split('\n')
            last_line = lines[-1].strip()
            if '=' in last_line and last_line.split('=')[0].strip():  # 确实是赋值语句
                var_name = last_line.split('=')[0].strip()
                result = execution_env.get(var_name)
            else:
                result = execution_env.get('result')
        else:
            # 对于表达式，使用eval执行
            result = eval(cleaned_code.strip(), execution_env)
        
        return {"result": result, "success": True}
            
    except Exception as e:
        # 检查是否是关于tuple的错误 - 包括多种可能的错误信息
        error_message = str(e)
        if ("Cannot subset columns with a tuple with more than one element" in error_message or 
            "Use a list instead" in error_message or
            "tuple indices must be integers or slices" in error_message or
            # 也处理直接的KeyError错误，这在某些pandas版本中出现
            (isinstance(e, KeyError) and isinstance(e.args[0], tuple) and len(e.args[0]) > 1)):
            try:
                # 尝试修复代码中的元组问题
                fixed_code = _fix_dataframe_column_access(cleaned_code)
                
                # 重新执行修复后的代码
                execution_env = {
                    'pd': pd,
                    'np': np,
                    'df': df
                }
                
                # 同样使用改进的赋值检测逻辑
                def has_assignment(code_str):
                    """检查代码中是否包含赋值语句（不在括号内的等号）"""
                    paren_level = 0
                    i = 0
                    while i < len(code_str):
                        char = code_str[i]
                        if char == '(':
                            paren_level += 1
                        elif char == ')':
                            paren_level -= 1
                        elif char == '=' and paren_level == 0:
                            # 检查等号前的字符，确保是真正的赋值
                            j = i - 1
                            while j >= 0 and code_str[j].isspace():
                                j -= 1
                            if j >= 0 and code_str[j] != ')' and code_str[j] != '(':
                                return True
                        i += 1
                    return False
                
                if has_assignment(fixed_code.strip()):
                    exec(fixed_code.strip(), execution_env)
                    lines = fixed_code.strip().split('\n')
                    last_line = lines[-1].strip()
                    if '=' in last_line and last_line.split('=')[0].strip():
                        var_name = last_line.split('=')[0].strip()
                        result = execution_env.get(var_name)
                    else:
                        result = execution_env.get('result')
                else:
                    result = eval(fixed_code.strip(), execution_env)
                
                logger.info(f"成功修复并执行了包含列选择问题的代码")
                return {"result": result, "success": True}
            except Exception as fix_error:
                logger.error(f"修复后的代码执行仍然失败: {str(fix_error)}")
                return {"error": str(fix_error), "success": False}
        # 检查是否是由于pandas操作返回了None
        elif "pivot_table" in code or "groupby" in code:
            try:
                # 再次尝试执行原始代码，但这次使用正确的判断逻辑
                execution_env = {
                    'pd': pd,
                    'np': np,
                    'df': df
                }
                
                # 尝试直接eval带修复的代码
                fixed_code = _fix_dataframe_column_access(cleaned_code)
                
                def has_assignment(code_str):
                    """检查代码中是否包含赋值语句（不在括号内的等号）"""
                    paren_level = 0
                    i = 0
                    while i < len(code_str):
                        char = code_str[i]
                        if char == '(':
                            paren_level += 1
                        elif char == ')':
                            paren_level -= 1
                        elif char == '=' and paren_level == 0:
                            j = i - 1
                            while j >= 0 and code_str[j].isspace():
                                j -= 1
                            if j >= 0 and code_str[j] != ')' and code_str[j] != '(':
                                return True
                        i += 1
                    return False
                
                if has_assignment(fixed_code.strip()):
                    exec(fixed_code.strip(), execution_env)
                    lines = fixed_code.strip().split('\n')
                    last_line = lines[-1].strip()
                    if '=' in last_line and last_line.split('=')[0].strip():
                        var_name = last_line.split('=')[0].strip()
                        result = execution_env.get(var_name)
                    else:
                        result = execution_env.get('result')
                else:
                    result = eval(fixed_code.strip(), execution_env)
                
                # 检查结果是否为None
                if result is not None:
                    logger.info(f"成功执行了pandas操作，结果类型: {type(result)}")
                    return {"result": result, "success": True}
                else:
                    # 如果结果是None，记录日志但继续
                    logger.warning(f"pandas操作执行成功但返回了None: {fixed_code}")
                    # 尝试执行一个简单的测试来确认pandas是否正常工作
                    test_result = eval("df.head(1)", execution_env)
                    if test_result is not None:
                        logger.info("pandas环境正常，问题可能在特定操作上")
                        # 重新尝试执行原始操作
                        if has_assignment(fixed_code.strip()):
                            exec(fixed_code.strip(), execution_env)
                            lines = fixed_code.strip().split('\n')
                            last_line = lines[-1].strip()
                            if '=' in last_line and last_line.split('=')[0].strip():
                                var_name = last_line.split('=')[0].strip()
                                result = execution_env.get(var_name)
                            else:
                                result = execution_env.get('result')
                        else:
                            result = eval(fixed_code.strip(), execution_env)
                        return {"result": result, "success": True}
            except Exception as pandas_error:
                logger.error(f"pandas操作处理失败: {str(pandas_error)}")
        
        logger.error(f"执行生成的代码时出错: {str(e)}")
        return {"error": str(e), "success": False}


def _fix_dataframe_column_access(code: str) -> str:
    """
    修复pandas DataFrame中元组用于多列选择的问题
    将代码中类似 df[(col1, col2)] 或 .groupby((col1, col2)) 的用法改为 df[[col1, col2]] 或 .groupby([col1, col2])
    """
    import re
    
    # 修复 df[(col1, col2)] 这种模式 -> df[[col1, col2]]
    fixed_code = re.sub(
        r'df\s*\[\s*\(\s*([^)]+?)\s*\)\s*\]', 
        r'df[[\1]]', 
        code
    )
    
    # 修复 .groupby((列名, 列名)) 这种模式 -> .groupby([列名, 列名])
    fixed_code = re.sub(
        r'(\.groupby\s*\(\s*)\(\s*([^)]+?)\s*\)(\s*\))',
        r'\1[\2]\3',  # 修复groupby的元组参数
        fixed_code
    )
    
    # 修复 .agg((函数, 函数)) 这种模式 -> .agg([函数, 函数])
    fixed_code = re.sub(
        r'(\.agg\s*\(\s*)\(\s*([^)]+?)\s*\)(\s*\))',
        r'\1[\2]\3',  # 修复agg的元组参数
        fixed_code
    )
    
    # 修复 .pivot_table 中 index 参数的元组使用
    fixed_code = re.sub(
        r'(\.pivot_table\s*\(.*?index\s*=\s*)\(\s*([^)]+?)\s*\)(\s*[,\)])',
        r'\1[\2]\3',
        fixed_code
    )
    
    # 修复 .pivot_table 中 columns 参数的元组使用
    fixed_code = re.sub(
        r'(\.pivot_table\s*\(.*?columns\s*=\s*)\(\s*([^)]+?)\s*\)(\s*[,\)])',
        r'\1[\2]\3',
        fixed_code
    )
    
    # 修复 .pivot_table 中 values 参数的元组使用
    fixed_code = re.sub(
        r'(\.pivot_table\s*\(.*?values\s*=\s*)\(\s*([^)]+?)\s*\)(\s*[,\)])',
        r'\1[\2]\3',
        fixed_code
    )
    
    return fixed_code


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
                has_cross_sheet_analysis = any("Sheet" in col for col in task_columns) or \
                                          len([col for col in task_columns if "编码" in col or "ID" in col or "id" in col]) > 1
                                          
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
            if isinstance(op_column, list) and any("Sheet" in col for col in op_column):
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
                        # 获取所有列名（不使用硬编码的关键词）
                        first_cols = list(first_df.columns)
                        second_cols = list(second_df.columns)
                        
                        # 如果存在列，则使用第一个列作为主要标识列
                        if first_cols and second_cols:
                            first_main_col = first_cols[0]  # 使用第一个列
                            second_main_col = second_cols[0]  # 使用第一个列
                            
                            # 重命名主要列
                            first_rename_dict = {first_main_col: f"{first_sheet_name}_{first_main_col}"}
                            second_rename_dict = {second_main_col: f"{second_sheet_name}_{second_main_col}"}
                            
                            # 重命名其他列
                            for col in first_cols[1:]:
                                first_rename_dict[col] = f"{first_sheet_name}_{col}"
                            for col in second_cols[1:]:
                                second_rename_dict[col] = f"{second_sheet_name}_{col}"
                            
                            first_df_renamed = first_df.rename(columns=first_rename_dict)
                            second_df_renamed = second_df.rename(columns=second_rename_dict)
                            
                            # 尝试合并两个DataFrame
                            first_df_renamed['_period'] = first_sheet_name
                            second_df_renamed['_period'] = second_sheet_name
                            
                            current_df = pd.concat([first_df_renamed, second_df_renamed], ignore_index=True)
                        else:
                            # 如果没有列，使用原始DataFrame
                            first_df['_period'] = first_sheet_name
                            second_df['_period'] = second_sheet_name
                            current_df = pd.concat([first_df, second_df], ignore_index=True)
            
            # 为了匹配操作中指定的列名，我们可能需要更新当前操作的列名映射
            # 如果操作指定的列名包含工作表前缀，但当前DataFrame没有，则需要映射
            op_column = op.get("column", [])
            if isinstance(op_column, list):
                # 检查操作中是否包含带前缀的列名
                prefixed_columns = [col for col in op_column if '_' in col and col.split('_')[0] in ['Sheet1', 'Sheet2', 'Sheet3', 'Sheet4', 'Sheet5', '工作表1', '工作表2', '工作表3', '工作表4', '工作表5']]
                if prefixed_columns:
                    # 创建列名映射：将带前缀的列名映射到当前DataFrame的实际列名
                    # 例如：'Sheet1_汇款国家/地区' -> '汇款国家/地区'
                    current_cols = list(current_df.columns)
                    column_mapping = {}
                    
                    for prefixed_col in prefixed_columns:
                        if '_' in prefixed_col:
                            actual_col = '_'.join(prefixed_col.split('_')[1:])  # 移除第一个下划线前的部分
                            # 在当前列中查找匹配项
                            for curr_col in current_cols:
                                if curr_col == actual_col or curr_col.endswith(actual_col):
                                    column_mapping[prefixed_col] = curr_col
                                    break
                    
                    # 更新操作中的列名以匹配当前DataFrame的实际列名
                    if column_mapping:
                        updated_op = op.copy()
                        if 'column' in updated_op and isinstance(updated_op['column'], list):
                            updated_columns = []
                            for col in updated_op['column']:
                                if col in column_mapping:
                                    updated_columns.append(column_mapping[col])
                                else:
                                    # 如果找不到映射，尝试直接使用（可能已经是正确名称）
                                    updated_columns.append(col)
                            updated_op['column'] = updated_columns
                        op = updated_op
            # 也处理字典类型的列参数（如pivot_table的index, columns, values）
            elif isinstance(op_column, dict):
                # 检查字典中的列名是否包含前缀
                current_cols = list(current_df.columns)
                updated_op = op.copy()
                updated_column_dict = {}
                
                for key, value in op_column.items():
                    if isinstance(value, str) and '_' in value and value.split('_')[0] in ['Sheet1', 'Sheet2', 'Sheet3', 'Sheet4', 'Sheet5', '工作表1', '工作表2', '工作表3', '工作表4', '工作表5']:
                        # 这是一个带前缀的列名，需要映射
                        actual_col = '_'.join(value.split('_')[1:])
                        for curr_col in current_cols:
                            if curr_col == actual_col or curr_col.endswith(actual_col):
                                updated_column_dict[key] = curr_col
                                break
                    elif isinstance(value, list):
                        # 处理列表类型的值（如values参数）
                        updated_list = []
                        for item in value:
                            if isinstance(item, str) and '_' in item and item.split('_')[0] in ['Sheet1', 'Sheet2', 'Sheet3', 'Sheet4', 'Sheet5', '工作表1', '工作表2', '工作表3', '工作表4', '工作表5']:
                                actual_col = '_'.join(item.split('_')[1:])
                                for curr_col in current_cols:
                                    if curr_col == actual_col or curr_col.endswith(actual_col):
                                        updated_list.append(curr_col)
                                        break
                            else:
                                updated_list.append(item)
                        updated_column_dict[key] = updated_list
                    else:
                        updated_column_dict[key] = value
                
                updated_op['column'] = updated_column_dict
                op = updated_op

            # 使用大模型生成代码来执行操作
            user_request = f"""
            你是一个pandas专家，基于以下任务计划和数据，生成对应的pandas代码：
            
            操作: {op}
            数据列: {list(current_df.columns)}
            
            请生成直接可用的pandas代码，用于执行该操作。
            代码应该只包含计算逻辑，不要包含函数定义。
            可用的变量是df（DataFrame）。
            """
            
            from .qwen_engine import create_model_params
            model_params = create_model_params(
                settings=settings or {},
                api_key=api_key,
                default_model='qwen-max',
                default_temperature=0.1,
                default_max_tokens=1024,
                default_top_p=0.8,
                default_frequency_penalty=0.5
            )
            
            # 生成代码
            generated_code = chat_with_llm(user_request, **model_params)
            
            # 清理并执行生成的代码
            execution_result = execute_generated_code(generated_code, current_df)
            
            if execution_result["success"]:
                results[f"{op_name}_result"] = _convert_pandas_types(execution_result["result"])
            else:
                # 如果执行失败，记录错误信息但继续处理其他操作
                error_msg = execution_result['error']
                results[f"{op_name}_error"] = f"代码执行错误: {error_msg}"
                logger.warning(f"操作 {op_name} 执行失败: {error_msg}")
                
        except Exception as e:
            # 捕获所有异常，记录错误但继续处理其他操作
            error_msg = str(e)
            results[op.get("name", "unknown")] = f"处理错误: {error_msg}"
            logger.error(f"处理操作 {op} 时出错: {error_msg}")
    
    return results


def _handle_cross_sheet_operations(multi_sheet_data, task_plan, api_key, settings):
    """
    处理跨工作表操作，如客户留存分析等
    """
    # 创建一个DataFrame来存储跨工作表分析结果
            # 这里我们假设工作表的结构相似，例如都是包含ID和分类信息的表
    
    if len(multi_sheet_data) < 2:
        # 如果只有一个工作表，返回该工作表的数据
        return list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()
    
    # 获取工作表名称列表
    sheet_names = list(multi_sheet_data.keys())
    
                            # 假设我们要比较第一个和第二个工作表
    if len(sheet_names) >= 2:
        first_sheet_name = sheet_names[0]
        second_sheet_name = sheet_names[1]
        
        first_df = multi_sheet_data[first_sheet_name].copy()
        second_df = multi_sheet_data[second_sheet_name].copy()
        
        # 获取第一列作为标识列（通常第一列是ID或编码列），而不是硬编码关键词
        first_cols = list(first_df.columns)
        second_cols = list(second_df.columns)
        
        if first_cols and second_cols:
            first_id_col = first_cols[0]  # 使用第一个列
            second_id_col = second_cols[0]  # 使用第一个列
            
            # 获取其他列（可能是分类列或其他属性列）
            first_other_cols = first_cols[1:]
            second_other_cols = second_cols[1:]
            
            # 为每个DataFrame添加工作表标识
            rename_dict = {first_id_col: f"{first_sheet_name}_{first_id_col}"}
            # 重命名其他列
            for col in first_other_cols:
                rename_dict[col] = f"{first_sheet_name}_{col}"
            
            first_df_renamed = first_df.rename(columns=rename_dict)
            
            rename_dict = {second_id_col: f"{second_sheet_name}_{second_id_col}"}
            # 重命名其他列
            for col in second_other_cols:
                rename_dict[col] = f"{second_sheet_name}_{col}"
            
            second_df_renamed = second_df.rename(columns=rename_dict)
            
            # 重命名后重新获取列名
            first_id_col_renamed = f"{first_sheet_name}_{first_id_col}"
            second_id_col_renamed = f"{second_sheet_name}_{second_id_col}"
            
            # 获取两个时间点的项集合
            first_items = set(first_df_renamed[first_id_col_renamed].dropna())
            second_items = set(second_df_renamed[second_id_col_renamed].dropna())
            
            # 计算留存、新增、流失项
            retained_items = first_items & second_items  # 两个时间点都有的项
            new_items = second_items - first_items       # 新增项
            lost_items = first_items - second_items      # 流失项
            
            # 创建留存分析结果DataFrame
            retention_data = {
                'retained_items_count': [len(retained_items)],
                'new_items_count': [len(new_items)],
                'lost_items_count': [len(lost_items)],
                'first_period_total': [len(first_items)],
                'second_period_total': [len(second_items)],
                'retention_rate': [len(retained_items) / len(first_items) if len(first_items) > 0 else 0]
            }
            
            # 创建一个包含留存分析结果的DataFrame
            result_df = pd.DataFrame(retention_data)
            
            # 如果存在其他列，添加原始数据的统计信息
            if first_other_cols and second_other_cols:
                # 使用第一个其他列作为分组列（比如分类列或任何其他分组列）
                first_group_col = f"{first_sheet_name}_{first_other_cols[0]}"
                second_group_col = f"{second_sheet_name}_{second_other_cols[0]}"
                
                # 按分组列统计各时间点的数量
                try:
                    first_group_counts = first_df_renamed[first_group_col].value_counts() if first_group_col in first_df_renamed.columns else pd.Series([], dtype=object)
                    second_group_counts = second_df_renamed[second_group_col].value_counts() if second_group_col in second_df_renamed.columns else pd.Series([], dtype=object)
                    
                    # 合并统计结果
                    if not first_group_counts.empty and not second_group_counts.empty:
                        group_comparison = pd.DataFrame({
                            f'{first_sheet_name}_count': first_group_counts,
                            f'{second_sheet_name}_count': second_group_counts
                        }).fillna(0)
                        
                        # 将分组比较数据添加到结果中
                        for group in group_comparison.index:
                            result_df[f'{group}_change'] = group_comparison.loc[group, f'{second_sheet_name}_count'] - \
                                                          group_comparison.loc[group, f'{first_sheet_name}_count']
                    elif not first_group_counts.empty:
                        group_comparison = pd.DataFrame({
                            f'{first_sheet_name}_count': first_group_counts
                        })
                        for group in group_comparison.index:
                            result_df[f'{group}_change'] = -group_comparison.loc[group, f'{first_sheet_name}_count']
                    elif not second_group_counts.empty:
                        group_comparison = pd.DataFrame({
                            f'{second_sheet_name}_count': second_group_counts
                        })
                        for group in group_comparison.index:
                            result_df[f'{group}_change'] = group_comparison.loc[group, f'{second_sheet_name}_count']
                except:
                    # 如果分组统计失败，跳过这部分
                    pass
            
            # 同时创建一个合并的DataFrame，其中包含所有跨工作表的信息
            # 为每个DataFrame添加工作表标签
            first_df_with_label = first_df_renamed.copy()
            first_df_with_label['_period'] = first_sheet_name
            second_df_with_label = second_df_renamed.copy()
            second_df_with_label['_period'] = second_sheet_name
            
            # 合并两个数据框
            combined_df = pd.concat([first_df_with_label, second_df_with_label], ignore_index=True)
            
            # 添加留存分析结果到合并的DataFrame
            for col, val in retention_data.items():
                combined_df[col] = val[0] if isinstance(val, list) else val
            
            return combined_df
        else:
            # 如果没有找到列，返回第一个工作表的数据
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
