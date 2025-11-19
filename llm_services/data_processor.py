# -*- coding: utf-8 -*-
"""
数据处理器模块
用于执行从商业角度透视数据的具体计算任务
"""

import pandas as pd
import numpy as np
from io import StringIO

# 操作函数注册表
OPERATION_REGISTRY = {}

def register_operation(name):
    """
    装饰器：用于注册操作函数
    
    Args:
        name (str): 操作名称
    """
    def decorator(func):
        OPERATION_REGISTRY[name] = func
        return func
    return decorator

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
        if line.startswith('工作表: '):
            # 如果之前有数据，保存之前的表格
            if current_sheet_name and sheet_data:
                try:
                    # 将数据转换为DataFrame
                    df_str = '\n'.join(sheet_data)
                    df = pd.read_csv(StringIO(df_str), sep='\s+', engine='python')
                    parsed_dataframes[current_sheet_name] = df
                except:
                    # 如果解析失败，尝试其他方法
                    try:
                        df = pd.read_csv(StringIO(df_str))
                        parsed_dataframes[current_sheet_name] = df
                    except:
                        print(f"无法解析工作表 {current_sheet_name} 的数据")
                        
            # 开始新工作表
            current_sheet_name = line.split('工作表: ')[1].strip()
            sheet_data = []
        else:
            # 如果不是空行，添加到当前工作表数据
            if line.strip():
                sheet_data.append(line)
    
    # 处理最后一个工作表的数据
    if current_sheet_name and sheet_data:
        try:
            df_str = '\n'.join(sheet_data)
            df = pd.read_csv(StringIO(df_str), sep='\s+', engine='python')
            parsed_dataframes[current_sheet_name] = df
        except:
            try:
                df = pd.read_csv(StringIO(df_str))
                parsed_dataframes[current_sheet_name] = df
            except:
                print(f"无法解析工作表 {current_sheet_name} 的数据")
    
    return parsed_dataframes

def process_data(task_plan, file_content=None):
    """
    根據任務計劃執行數據處理，從商業角度透視數據
    
    Args:
        task_plan (dict): 任務計劃
        file_content (str): 文件內容
        
    Returns:
        dict: 計算結果
    """
    
    # 如果沒有文件內容，創建示例數據
    if not file_content:
        # 創建示例數據
        data = {
            '日期': pd.date_range('2023-01-01', periods=12, freq='M'),
            '銷售額': [1000, 1200, 1100, 1300, 1250, 1400, 1500, 1450, 1600, 1550, 1700, 1800],
            '成本': [600, 700, 650, 750, 720, 800, 850, 820, 900, 880, 950, 1000],
            '利潤': [400, 500, 450, 550, 530, 600, 650, 630, 700, 670, 750, 800]
        }
        df = pd.DataFrame(data)
        multi_sheet_data = None
    else:
        # 檢查是否是多工作表數據（包含"工作表: "標記）
        if "工作表: " in file_content:
            # 解析多工作表數據
            multi_sheet_data = parse_multi_sheet_data(file_content)
            # 使用第一個工作表作為默認數據框
            df = list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()
        else:
            # 尝试解析文件内容为DataFrame
            df = None
            multi_sheet_data = None
            # 首先尝试作为CSV格式读取
            try:
                df = pd.read_csv(StringIO(file_content))
            except:
                pass
                
            # 检查第一行是否包含制表符，如果是则强制使用制表符分隔
            if file_content and '\t' in file_content.split('\n')[0]:
                try:
                    # 强制使用制表符分隔
                    df = pd.read_csv(StringIO(file_content), sep='\t')
                except:
                    pass
            # 如果数据看起来是用空格分隔的（多个连续空格）
            elif file_content and '  ' in file_content.split('\n')[0]:  # 检查是否有多个连续空格
                try:
                    # 使用正则表达式分隔多个空格
                    df = pd.read_csv(StringIO(file_content), sep='\s+', engine='python')
                except:
                    pass
                    
            if df is None:
                try:
                    # 尝试作为制表符分隔的文件读取
                    df = pd.read_csv(StringIO(file_content), sep='\t')
                except:
                    pass
                
        if df is None:
            try:
                # 如果不是CSV或TSV，嘗試作為製表符分隔的文本處理
                lines = file_content.strip().split('\n')
                if len(lines) > 1:
                    # 檢查是否是製表符分隔的文件
                    first_line = lines[0]
                    if '\t' in first_line:
                        # 處理製表符分隔的文件
                        headers = first_line.split('\t')
                        # 清理列名中的多餘空格
                        headers = [header.strip() for header in headers]
                        data_lines = []
                        for line in lines[1:]:
                            fields = line.split('\t')
                            # 確保數據行的字段數與表頭數一致
                            if len(fields) >= len(headers):
                                # 只取與表頭數量相同的字段
                                data_lines.append(fields[:len(headers)])
                            else:
                                # 如果字段數不足，用空字符串填充
                                padded_fields = fields + [''] * (len(headers) - len(fields))
                                data_lines.append(padded_fields)
                        # 清理數據行中的多餘空格
                        cleaned_data_lines = []
                        for line in data_lines:
                            cleaned_line = [item.strip() for item in line]
                            cleaned_data_lines.append(cleaned_line)
                        df = pd.DataFrame(cleaned_data_lines, columns=headers)
                    elif ',' in first_line:
                        # 處理逗號分隔的文件
                        headers = first_line.split(',')
                        # 清理列名中的多餘空格
                        headers = [header.strip() for header in headers]
                        data_lines = []
                        for line in lines[1:]:
                            fields = line.split(',')
                            # 確保數據行的字段數與表頭數一致
                            if len(fields) >= len(headers):
                                # 只取與表頭數量相同的字段
                                data_lines.append(fields[:len(headers)])
                            else:
                                # 如果字段數不足，用空字符串填充
                                padded_fields = fields + [''] * (len(headers) - len(fields))
                                data_lines.append(padded_fields)
                        # 清理數據行中的多餘空格
                        cleaned_data_lines = []
                        for line in data_lines:
                            cleaned_line = [item.strip() for item in line]
                            cleaned_data_lines.append(cleaned_line)
                        df = pd.DataFrame(cleaned_data_lines, columns=headers)
                    elif '|' in first_line:
                        # 處理管道符分隔的文件
                        headers = first_line.split('|')
                        # 清理列名中的多餘空格
                        headers = [header.strip() for header in headers]
                        data_lines = []
                        for line in lines[1:]:
                            fields = line.split('|')
                            # 確保數據行的字段數與表頭數一致
                            if len(fields) >= len(headers):
                                # 只取與表頭數量相同的字段
                                data_lines.append(fields[:len(headers)])
                            else:
                                # 如果字段數不足，用空字符串填充
                                padded_fields = fields + [''] * (len(headers) - len(fields))
                                data_lines.append(padded_fields)
                        # 清理數據行中的多餘空格
                        cleaned_data_lines = []
                        for line in data_lines:
                            cleaned_line = [item.strip() for item in line]
                            cleaned_data_lines.append(cleaned_line)
                        df = pd.DataFrame(cleaned_data_lines, columns=headers)
                    else:
                        # 如果沒有明顯的分隔符，嘗試根據空格分割，但保留原始列名
                        # 這裡處理複雜的情況，如列名裡包含多個信息
                        # 清理列名中的多餘空格
                        cleaned_first_line = ' '.join(first_line.split())
                        headers = [cleaned_first_line]
                        data_lines = [[line.strip()] for line in lines[1:]]
                        df = pd.DataFrame(data_lines, columns=headers)
                        
                        # 進一步處理列名，嘗試提取實際的列名
                        if len(headers) == 1 and ' ' in headers[0]:
                            # 如果列名中包含空格，嘗試提取有意義的部分
                            original_column = headers[0]
                            # 移除多餘的空格
                            cleaned_column = ' '.join(original_column.split())
                            df.columns = [cleaned_column]
                else:
                    # 只有一行數據
                    df = pd.DataFrame([file_content.split(',')])
            except Exception as e:
                # 如果都失敗了，返回錯誤
                return {
                    "error": f"無法解析文件內容: {str(e)}",
                    "results": {}
                }
        else:
            print("成功使用pandas讀取數據")
            print("列名:", df.columns.tolist())
        
        # 嘗試將所有列轉換為數值類型，如果可能的話
        # 但如果是多工作表数据，跳过这个步骤，因为每个工作表会单独处理
        if not multi_sheet_data:
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    # 如果轉換失敗，保持原值
                    pass
    
    # 清理所有列名中的多余空格
    df.columns = [col.strip() for col in df.columns]
    
    # 执行计算任务
    results = {}
    
    # 确定需要处理的列 - 包括任务计划中指定的列和操作中需要的列
    columns = task_plan.get("columns", [])
    
    # 收集所有操作中需要的列
    operation_columns = []
    operations = task_plan.get("operations", [])
    for op in operations:
        op_column = op.get("column")
        if op_column and not isinstance(op_column, (dict, list)):  # 只添加简单类型的列名
            operation_columns.append(op_column)
    
    # 合并任务计划列和操作列
    all_needed_columns = list(set(columns + operation_columns))
    
    # 如果是多工作表数据，需要特殊处理
    if multi_sheet_data:
        # 对于多工作表数据，我们需要处理"工作表名.列名"格式的列引用
        processed_operations = []
        for op in operations:
            op_column = op.get("column")
            if op_column and "." in op_column:
                # 分离工作表名和列名
                parts = op_column.split(".", 1)
                sheet_name, column_name = parts[0], parts[1]
                if sheet_name in multi_sheet_data:
                    # 为特定工作表创建操作
                    new_op = op.copy()  # 使用浅拷贝
                    new_op["column"] = column_name
                    new_op["_sheet"] = sheet_name  # 记录工作表名
                    processed_operations.append(new_op)
                else:
                    processed_operations.append(op)
            else:
                processed_operations.append(op)
        
        # 处理每个操作
        for op in processed_operations:
            try:
                op_name = op.get("name")
                column = op.get("column")
                sheet_name = op.get("_sheet")  # 获取指定的工作表
                
                # 确定使用哪个数据框
                current_df = multi_sheet_data.get(sheet_name, df) if sheet_name else df
                
                # 尝试匹配列名（只对字符串类型的列名进行匹配）
                actual_column = None
                if column and isinstance(column, str):
                    # 首先尝试精确匹配（忽略空格）
                    stripped_column = column.strip()
                    for col in current_df.columns:
                        if stripped_column == col.strip():
                            actual_column = col
                            break
                    
                    # 如果没有精确匹配，尝试模糊匹配
                    if not actual_column:
                        for col in current_df.columns:
                            if stripped_column in col or col in stripped_column:
                                actual_column = col
                                break
                
                if column and not actual_column and isinstance(column, str):
                    column_ref = f"{sheet_name}.{column}" if sheet_name else column
                    results[f"{op_name}_{column_ref}"] = f"错误：列 '{column_ref}' 不存在"
                    continue
                    
                # 使用注册的操作处理函数
                if op_name in OPERATION_REGISTRY:
                    operation_func = OPERATION_REGISTRY[op_name]
                    
                    # 检查是否需要复杂参数（如字典或列表）
                    if isinstance(column, (dict, list)) and op_name in ['group_by', 'pivot_table', 'cross_tab', 'aggregate']:
                        # 对于需要复杂参数的操作，传递原始参数
                        operation_result = operation_func(current_df, column)
                    else:
                        # 对于普通操作，传递匹配到的列名
                        operation_result = operation_func(current_df, actual_column if actual_column else current_df.columns.tolist())
                    
                    # 根据操作结果更新results字典
                    column_ref = f"{sheet_name}.{column}" if sheet_name and column else (column or "all")
                    if actual_column and not isinstance(column, (dict, list)):
                        # 如果指定了具体列，则添加列名前缀
                        if isinstance(operation_result, dict):
                            results[f"{column_ref}_"] = operation_result
                        else:
                            results[f"{column_ref}_{op_name}"] = operation_result
                    else:
                        # 如果没有指定列或使用了复杂参数，则使用操作名作为前缀
                        if isinstance(operation_result, dict):
                            results.update(operation_result)
                        else:
                            # 如果返回单个值，使用操作名存储
                            results[f"{op_name}_result"] = operation_result
                else:
                    # 如果操作未注册，返回错误信息
                    results[f"{op_name}_error"] = f"不支持的操作: {op_name}，请使用以下操作之一: {list(OPERATION_REGISTRY.keys())}"
                            
            except Exception as e:
                column_ref = op.get("column", "unknown")
                sheet_name = op.get("_sheet")
                full_column_ref = f"{sheet_name}.{column_ref}" if sheet_name else column_ref
                results[op.get("name", "unknown")] = f"计算错误: {str(e)} (列: {full_column_ref})"
    else:
        # 单工作表数据的处理逻辑（保持原有逻辑）
        # 如果指定了列，只处理这些列
        if all_needed_columns:
            # 只保留指定的列
            existing_columns = [col for col in all_needed_columns if col in df.columns]
            # 如果没有完全匹配的列，尝试模糊匹配
            if not existing_columns:
                for col in all_needed_columns:
                    for actual_col in df.columns:
                        # 如果任务规划中的列名是实际列名的一部分，或者反之
                        if col in actual_col or actual_col in col:
                            existing_columns.append(actual_col)
                            break
            
            if existing_columns:
                df = df[existing_columns]
        
        # 执行操作
        operations = task_plan.get("operations", [])
        
        for op in operations:
            try:
                op_name = op.get("name")
                column = op.get("column")
                
                # 尝试匹配列名（只对字符串类型的列名进行匹配）
                actual_column = None
                if column and isinstance(column, str):
                    # 首先尝试精确匹配（忽略空格）
                    stripped_column = column.strip()
                    for col in df.columns:
                        if stripped_column == col.strip():
                            actual_column = col
                            break
                    
                    # 如果没有精确匹配，尝试模糊匹配
                    if not actual_column:
                        for col in df.columns:
                            if stripped_column in col or col in stripped_column:
                                actual_column = col
                                break
                
                if column and not actual_column and isinstance(column, str):
                    results[f"{op_name}_{column}"] = f"错误：列 '{column}' 不存在"
                    continue
                    
                # 使用注册的操作处理函数
                if op_name in OPERATION_REGISTRY:
                    operation_func = OPERATION_REGISTRY[op_name]
                    
                    # 检查是否需要复杂参数（如字典或列表）
                    if isinstance(column, (dict, list)) and op_name in ['group_by', 'pivot_table', 'cross_tab', 'aggregate']:
                        # 对于需要复杂参数的操作，传递原始参数
                        operation_result = operation_func(df, column)
                    else:
                        # 对于普通操作，传递匹配到的列名
                        operation_result = operation_func(df, actual_column if actual_column else df.columns.tolist())
                    
                    # 根据操作结果更新results字典
                    if actual_column and not isinstance(column, (dict, list)):
                        # 如果指定了具体列，则添加列名前缀
                        if isinstance(operation_result, dict):
                            results[f"{column}_"] = operation_result
                        else:
                            results[f"{column}_{op_name}"] = operation_result
                    else:
                        # 如果没有指定列或使用了复杂参数，则使用操作名作为前缀
                        if isinstance(operation_result, dict):
                            results.update(operation_result)
                        else:
                            # 如果返回单个值，使用操作名存储
                            results[f"{op_name}_result"] = operation_result
                else:
                    # 如果操作未注册，返回错误信息
                    results[f"{op_name}_error"] = f"不支持的操作: {op_name}，请使用以下操作之一: {list(OPERATION_REGISTRY.keys())}"
                            
            except Exception as e:
                results[op_name] = f"计算错误: {str(e)}"
    
    # 添加基本统计信息
    results["行数"] = len(df)
    results["列数"] = len(df.columns)
    results["列名"] = list(df.columns)
    
    return {
        "task_type": task_plan.get("task_type", "未知任务"),
        "results": results
    }


# 注册操作函数
@register_operation("mean")
def mean_operation(df, columns):
    """
    计算平均值操作，用于了解业务指标的平均水平
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 平均值结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算平均值
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_平均值"] = float(df[col].mean())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_平均值"] = np.nan
        return result
    else:
        # 对指定列计算平均值
        try:
            return float(df[columns].mean())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("sum")
def sum_operation(df, columns):
    """
    计算总和操作，用于了解业务指标的总体规模
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 总和结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算总和
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_总和"] = float(df[col].sum())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回0
                result[f"{col}_总和"] = 0.0
        return result
    else:
        # 对指定列计算总和
        try:
            return float(df[columns].sum())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回0
            return 0.0


@register_operation("max")
def max_operation(df, columns):
    """
    计算最大值操作，用于识别业务中的峰值表现
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 最大值结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算最大值
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_最大值"] = float(df[col].max())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_最大值"] = np.nan
        return result
    else:
        # 对指定列计算最大值
        try:
            return float(df[columns].max())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("min")
def min_operation(df, columns):
    """
    计算最小值操作，用于识别业务中的最低表现
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 最小值结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算最小值
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_最小值"] = float(df[col].min())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_最小值"] = np.nan
        return result
    else:
        # 对指定列计算最小值
        try:
            return float(df[columns].min())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("count")
def count_operation(df, columns):
    """
    计算计数操作，用于了解数据覆盖范围
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or int: 计数结果
    """
    if isinstance(columns, list):
        # 对所有列计算计数
        result = {}
        for col in df.columns:
            try:
                result[f"{col}_计数"] = int(df[col].count())
            except (ValueError, TypeError):
                # 如果无法转换为整数，返回0
                result[f"{col}_计数"] = 0
        return result
    else:
        # 对指定列计算计数
        try:
            return int(df[columns].count())
        except (ValueError, TypeError):
            # 如果无法转换为整数，返回0
            return 0


@register_operation("percentage")
def percentage_operation(df, columns):
    """
    计算百分比操作，用于分析业务构成比例
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict: 百分比结果
    """
    if isinstance(columns, list):
        # 对所有列计算百分比
        result = {}
        for col in df.columns:
            value_counts = df[col].value_counts()
            total_count = len(df[col])
            percentage_data = {}
            for value, count in value_counts.items():
                percentage = (count / total_count) * 100
                percentage_data[f"{value}_百分比"] = round(percentage, 2)
            result[f"{col}_百分比"] = percentage_data
        return result
    else:
        # 对指定列计算百分比
        value_counts = df[columns].value_counts()
        total_count = len(df[columns])
        percentage_data = {}
        for value, count in value_counts.items():
            percentage = (count / total_count) * 100
            percentage_data[f"{value}_百分比"] = round(percentage, 2)
        return {f"{columns}_百分比": percentage_data}


@register_operation("std")
def std_operation(df, columns):
    """
    计算标准差操作，用于评估业务指标的波动性
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 标准差结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算标准差
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_标准差"] = float(df[col].std())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_标准差"] = np.nan
        return result
    else:
        # 对指定列计算标准差
        try:
            return float(df[columns].std())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("unique")
def unique_operation(df, columns):
    """
    计算唯一值操作，用于了解业务分类的多样性
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or list: 唯一值结果
    """
    if isinstance(columns, list):
        # 对所有列计算唯一值
        result = {}
        for col in df.columns:
            unique_values = df[col].unique().tolist()
            result[f"{col}_唯一值"] = unique_values
        return result
    else:
        # 对指定列计算唯一值
        return df[columns].unique().tolist()


@register_operation("median")
def median_operation(df, columns):
    """
    计算中位数操作，用于了解业务指标的中间水平
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 中位数结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算中位数
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_中位数"] = float(df[col].median())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_中位数"] = np.nan
        return result
    else:
        # 对指定列计算中位数
        try:
            return float(df[columns].median())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("mode")
def mode_operation(df, columns):
    """
    计算众数操作，用于识别最常见的业务情况
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or list: 众数结果
    """
    if isinstance(columns, list):
        # 对所有列计算众数
        result = {}
        for col in df.columns:
            mode_values = df[col].mode().tolist()
            result[f"{col}_众数"] = mode_values
        return result
    else:
        # 对指定列计算众数
        return df[columns].mode().tolist()


@register_operation("variance")
def variance_operation(df, columns):
    """
    计算方差操作，用于评估业务指标的离散程度
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 方差结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算方差
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_方差"] = float(df[col].var())
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_方差"] = np.nan
        return result
    else:
        # 对指定列计算方差
        try:
            return float(df[columns].var())
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("quantile_25")
def quantile_25_operation(df, columns):
    """
    计算25%分位数操作，用于了解业务指标的低分段表现
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 25%分位数结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算25%分位数
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_25分位数"] = float(df[col].quantile(0.25))
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_25分位数"] = np.nan
        return result
    else:
        # 对指定列计算25%分位数
        try:
            return float(df[columns].quantile(0.25))
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("quantile_75")
def quantile_75_operation(df, columns):
    """
    计算75%分位数操作，用于了解业务指标的高分段表现
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 75%分位数结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算75%分位数
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                result[f"{col}_75分位数"] = float(df[col].quantile(0.75))
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_75分位数"] = np.nan
        return result
    else:
        # 对指定列计算75%分位数
        try:
            return float(df[columns].quantile(0.75))
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("range")
def range_operation(df, columns):
    """
    计算数值范围（最大值-最小值）操作，用于了解业务指标的波动区间
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 范围结果
    """
    if isinstance(columns, list):
        # 对所有数值列计算范围
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            try:
                data_range = float(df[col].max()) - float(df[col].min())
                result[f"{col}_范围"] = data_range
            except (ValueError, TypeError):
                # 如果无法转换为数值，返回NaN
                result[f"{col}_范围"] = np.nan
        return result
    else:
        # 对指定列计算范围
        try:
            data_range = float(df[columns].max()) - float(df[columns].min())
            return data_range
        except (ValueError, TypeError):
            # 如果无法转换为数值，返回NaN
            return np.nan


@register_operation("first")
def first_operation(df, columns):
    """
    获取第一行数据操作，用于了解业务的起始状态
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or any: 第一行数据
    """
    if isinstance(columns, list):
        # 对所有列获取第一行数据
        result = {}
        for col in df.columns:
            if len(df) > 0:
                result[f"{col}_首行"] = df[col].iloc[0]
            else:
                result[f"{col}_首行"] = None
        return result
    else:
        # 对指定列获取第一行数据
        if len(df) > 0:
            return df[columns].iloc[0]
        else:
            return None


@register_operation("last")
def last_operation(df, columns):
    """
    获取最后一行数据操作，用于了解业务的最新状态
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or any: 最后一行数据
    """
    if isinstance(columns, list):
        # 对所有列获取最后一行数据
        result = {}
        for col in df.columns:
            if len(df) > 0:
                result[f"{col}_末行"] = df[col].iloc[-1]
            else:
                result[f"{col}_末行"] = None
        return result
    else:
        # 对指定列获取最后一行数据
        if len(df) > 0:
            return df[columns].iloc[-1]
        else:
            return None


@register_operation("missing_count")
def missing_count_operation(df, columns):
    """
    计算缺失值数量操作，用于评估数据完整性
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or int: 缺失值数量
    """
    if isinstance(columns, list):
        # 对所有列计算缺失值数量
        result = {}
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            result[f"{col}_缺失值数量"] = missing_count
        return result
    else:
        # 对指定列计算缺失值数量
        return int(df[columns].isna().sum())


@register_operation("missing_percentage")
def missing_percentage_operation(df, columns):
    """
    计算缺失值百分比操作，用于评估数据质量
    
    Args:
        df: DataFrame
        columns: 列名或列名列表
        
    Returns:
        dict or float: 缺失值百分比
    """
    if isinstance(columns, list):
        # 对所有列计算缺失值百分比
        result = {}
        for col in df.columns:
            total_count = len(df[col])
            missing_count = int(df[col].isna().sum())
            percentage = (missing_count / total_count) * 100 if total_count > 0 else 0
            result[f"{col}_缺失值百分比"] = round(percentage, 2)
        return result
    else:
        # 对指定列计算缺失值百分比
        total_count = len(df[columns])
        missing_count = int(df[columns].isna().sum())
        percentage = (missing_count / total_count) * 100 if total_count > 0 else 0
        return round(percentage, 2)


@register_operation("correlation")
def correlation_operation(df, columns):
    """
    计算数值列之间的相关性矩阵操作，用于识别业务指标间的关联性
    
    Args:
        df: DataFrame
        columns: 列名或列名列表（必须是数值列）
        
    Returns:
        dict or DataFrame: 相关性矩阵
    """
    if isinstance(columns, list):
        # 只对数值列计算相关性
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) < 2:
            return {"error": "至少需要两列数值数据才能计算相关性"}
        
        # 如果指定了特定的列，只计算这些列的相关性
        if set(columns).issubset(set(numeric_cols)):
            correlation_matrix = df[columns].corr()
        else:
            correlation_matrix = df[numeric_cols].corr()
        
        # 将相关性矩阵转换为字典格式
        result = {}
        for col1 in correlation_matrix.columns:
            result[col1] = {}
            for col2 in correlation_matrix.columns:
                result[col1][col2] = float(correlation_matrix.loc[col1, col2])
        return result
    else:
        # 单列无法计算相关性
        return {"error": "相关性操作需要至少两列数据"}


@register_operation("group_by")
def group_by_operation(df, columns):
    """
    分组操作，用于按指定列进行数据透视分析
    
    Args:
        df: DataFrame
        columns: 列名或列名列表（用于分组的列）
        
    Returns:
        dict: 分组后的统计结果
    """
    if isinstance(columns, list):
        # 如果是列表，使用所有指定的列进行分组
        if len(columns) == 0:
            return {"error": "请指定至少一个用于分组的列"}
        
        # 确保所有分组列都存在于DataFrame中
        existing_cols = []
        missing_cols = []
        for col in columns:
            found = False
            for df_col in df.columns:
                if col == df_col or col in df_col or df_col in col:
                    existing_cols.append(df_col)
                    found = True
                    break
            if not found:
                missing_cols.append(col)
        
        if missing_cols:
            return {"error": f"找不到以下列: {missing_cols}"}
        
        try:
            # 按指定列进行分组
            grouped = df.groupby(existing_cols)
            
            # 计算各种统计量
            result = {}
            # 计算数值列的统计量
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            numeric_cols = [col for col in numeric_cols if col not in existing_cols]  # 排除分组列
            
            if len(numeric_cols) > 0:
                # 为每个数值列计算聚合统计
                for col in numeric_cols:
                    col_result = {}
                    
                    # 总和
                    sum_result = grouped[col].sum()
                    if len(existing_cols) == 1:
                        col_result[f"{col}_sum"] = sum_result.to_dict()
                    else:
                        # 将元组键转换为字符串
                        sum_dict = sum_result.to_dict()
                        col_result[f"{col}_sum"] = {str(k): v for k, v in sum_dict.items()}
                    
                    # 平均值
                    mean_result = grouped[col].mean()
                    if len(existing_cols) == 1:
                        col_result[f"{col}_mean"] = mean_result.to_dict()
                    else:
                        # 将元组键转换为字符串
                        mean_dict = mean_result.to_dict()
                        col_result[f"{col}_mean"] = {str(k): v for k, v in mean_dict.items()}
                    
                    # 计数
                    count_result = grouped[col].count()
                    if len(existing_cols) == 1:
                        col_result[f"{col}_count"] = count_result.to_dict()
                    else:
                        # 将元组键转换为字符串
                        count_dict = count_result.to_dict()
                        col_result[f"{col}_count"] = {str(k): v for k, v in count_dict.items()}
                    
                    # 最大值
                    max_result = grouped[col].max()
                    if len(existing_cols) == 1:
                        col_result[f"{col}_max"] = max_result.to_dict()
                    else:
                        # 将元组键转换为字符串
                        max_dict = max_result.to_dict()
                        col_result[f"{col}_max"] = {str(k): v for k, v in max_dict.items()}
                    
                    # 最小值
                    min_result = grouped[col].min()
                    if len(existing_cols) == 1:
                        col_result[f"{col}_min"] = min_result.to_dict()
                    else:
                        # 将元组键转换为字符串
                        min_dict = min_result.to_dict()
                        col_result[f"{col}_min"] = {str(k): v for k, v in min_dict.items()}
                    
                    result.update(col_result)
            
            # 单独计算分组计数（即每个分组中有多少行）
            count_result = grouped.size()
            if len(existing_cols) == 1:
                result["group_counts"] = count_result.to_dict()
            else:
                # 将元组键转换为字符串
                count_dict = count_result.to_dict()
                result["group_counts"] = {str(k): v for k, v in count_dict.items()}
            
            return result
        except Exception as e:
            return {"error": f"分组操作失败: {str(e)}"}
    else:
        # 单列分组
        # 尝试匹配列名
        actual_column = None
        for col in df.columns:
            if columns == col or columns in col or col in columns:
                actual_column = col
                break
        
        if not actual_column:
            return {"error": f"找不到列: {columns}"}
        
        try:
            # 按指定列进行分组
            grouped = df.groupby(actual_column)
            
            # 计算各种统计量
            result = {}
            # 计算数值列的统计量
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            numeric_cols = [col for col in numeric_cols if col != actual_column]  # 排除分组列
            
            if len(numeric_cols) > 0:
                # 为每个数值列计算聚合统计
                for col in numeric_cols:
                    col_result = {}
                    
                    # 总和
                    sum_result = grouped[col].sum()
                    col_result[f"{col}_sum"] = sum_result.to_dict()
                    
                    # 平均值
                    mean_result = grouped[col].mean()
                    col_result[f"{col}_mean"] = mean_result.to_dict()
                    
                    # 最大值
                    max_result = grouped[col].max()
                    col_result[f"{col}_max"] = max_result.to_dict()
                    
                    # 最小值
                    min_result = grouped[col].min()
                    col_result[f"{col}_min"] = min_result.to_dict()
                    
                    result.update(col_result)
            
            # 分组计数
            count_result = grouped.size().to_dict()
            result["group_counts"] = count_result
            
            return result
        except Exception as e:
            return {"error": f"分组操作失败: {str(e)}"}


@register_operation("cross_tab")
def cross_tab_operation(df, columns):
    """
    交叉表操作，用于分析两个分类变量之间的关系
    
    Args:
        df: DataFrame
        columns: 包含两个列名的列表（用于创建交叉表）
        
    Returns:
        dict: 交叉表结果
    """
    if isinstance(columns, list):
        if len(columns) < 2:
            return {"error": "交叉表操作需要至少两列数据"}
        
        # 确保所有列都存在于DataFrame中
        existing_cols = []
        missing_cols = []
        for col in columns[:2]:  # 只取前两列
            found = False
            for df_col in df.columns:
                if col == df_col or col in df_col or df_col in col:
                    existing_cols.append(df_col)
                    found = True
                    break
            if not found:
                missing_cols.append(col)
        
        if missing_cols:
            return {"error": f"找不到以下列: {missing_cols}"}
        
        try:
            # 创建交叉表
            crosstab = pd.crosstab(df[existing_cols[0]], df[existing_cols[1]], margins=True)
            
            # 转换为字典格式，确保所有键都是字符串
            crosstab_dict = crosstab.to_dict()
            # 递归地将所有非字符串键转换为字符串
            def convert_keys_to_str(obj):
                if isinstance(obj, dict):
                    new_dict = {}
                    for k, v in obj.items():
                        new_k = str(k) if not isinstance(k, (str, int, float, bool)) else k
                        new_dict[new_k] = convert_keys_to_str(v) if isinstance(v, (dict, list)) else v
                    return new_dict
                elif isinstance(obj, list):
                    return [convert_keys_to_str(item) if isinstance(item, (dict, list)) else item for item in obj]
                else:
                    return obj
            
            result = {}
            result["交叉表"] = convert_keys_to_str(crosstab_dict)
            result["计数"] = convert_keys_to_str(crosstab_dict)
            
            # 同时计算百分比
            crosstab_pct = pd.crosstab(df[existing_cols[0]], df[existing_cols[1]], normalize='all', margins=True) * 100
            result["百分比"] = convert_keys_to_str(crosstab_pct.to_dict())
            
            return result
        except Exception as e:
            return {"error": f"交叉表操作失败: {str(e)}"}
    else:
        return {"error": "交叉表操作需要指定两列数据，请使用列表格式"}


@register_operation("aggregate")
def aggregate_operation(df, columns):
    """
    聚合操作，用于对分组数据进行多种统计计算
    
    Args:
        df: DataFrame
        columns: 包含分组列和聚合列的字典，格式为 {"group_by": ["col1", "col2"], "agg": {"col3": ["sum", "mean"], "col4": ["count", "max"]}}
        
    Returns:
        dict: 聚合结果
    """
    if isinstance(columns, dict):
        group_by_cols = columns.get("group_by", [])
        agg_dict = columns.get("agg", {})
        
        if not group_by_cols:
            return {"error": "请指定至少一个用于分组的列"}
        
        if not agg_dict:
            return {"error": "请指定聚合操作"}
        
        # 确保分组列都存在于DataFrame中
        existing_group_cols = []
        missing_group_cols = []
        for col in group_by_cols:
            found = False
            for df_col in df.columns:
                if col == df_col or col in df_col or df_col in col:
                    existing_group_cols.append(df_col)
                    found = True
                    break
            if not found:
                missing_group_cols.append(col)
        
        if missing_group_cols:
            return {"error": f"找不到以下分组列: {missing_group_cols}"}
        
        # 确保聚合列都存在于DataFrame中
        existing_agg_cols = {}
        missing_agg_cols = []
        for col, agg_funcs in agg_dict.items():
            found = False
            for df_col in df.columns:
                if col == df_col or col in df_col or df_col in col:
                    existing_agg_cols[df_col] = agg_funcs
                    found = True
                    break
            if not found:
                missing_agg_cols.append(col)
        
        if missing_agg_cols:
            return {"error": f"找不到以下聚合列: {missing_agg_cols}"}
        
        try:
            # 执行聚合操作
            result = {}
            grouped = df.groupby(existing_group_cols)
            
            # 重构聚合字典，使其符合pandas的格式
            agg_dict_for_pandas = {}
            for col, funcs in existing_agg_cols.items():
                if isinstance(funcs, list):
                    agg_dict_for_pandas[col] = funcs
                else:
                    agg_dict_for_pandas[col] = [funcs]
            
            agg_result = grouped.agg(agg_dict_for_pandas)
            
            # 转换为字典格式
            if isinstance(agg_result, pd.DataFrame):
                # 处理多级列索引
                if isinstance(agg_result.columns, pd.MultiIndex):
                    agg_dict_result = {}
                    for (col, func) in agg_result.columns:
                        key = f"{col}_{func}"
                        # 确保所有键都转换为字符串
                        agg_dict_result[key] = {str(k) if not isinstance(k, (str, int, float, bool)) else k: v 
                                               for k, v in agg_result[(col, func)].to_dict().items()}
                    result["聚合结果"] = agg_dict_result
                else:
                    # 确保所有键都转换为字符串
                    result["聚合结果"] = {str(k) if not isinstance(k, (str, int, float, bool)) else k: v 
                                        for k, v in agg_result.to_dict().items()}
            else:
                # 确保所有键都转换为字符串
                result["聚合结果"] = {str(k) if not isinstance(k, (str, int, float, bool)) else k: v 
                                    for k, v in agg_result.to_dict().items()}
            
            return result
        except Exception as e:
            return {"error": f"聚合操作失败: {str(e)}"}


@register_operation("pivot_table")
def pivot_table_operation(df, columns):
    """
    透视表操作，用于创建交叉汇总表
    
    Args:
        df: DataFrame
        columns: 包含行、列和值的字典，格式为 {"index": "行列名", "columns": "列名", "values": "值列名", "aggfunc": "聚合函数"}
        
    Returns:
        dict: 透视表结果
    """
    if isinstance(columns, dict):
        index_col = columns.get("index")
        column_col = columns.get("columns")
        value_col = columns.get("values")
        agg_func = columns.get("aggfunc", "sum")  # 默认使用sum函数
        
        # 查找匹配的列名
        actual_index_col = None
        actual_column_col = None
        actual_value_col = None
        
        for col in df.columns:
            if index_col and (index_col == col or index_col in col or col in index_col):
                actual_index_col = col
            if column_col and (column_col == col or column_col in col or col in column_col):
                actual_column_col = col
            if value_col and (value_col == col or value_col in col or col in value_col):
                actual_value_col = col
        
        if not actual_index_col:
            return {"error": f"找不到行分组列: {index_col}"}
        if not actual_column_col:
            return {"error": f"找不到列分组列: {column_col}"}
        if not actual_value_col:
            return {"error": f"找不到值列: {value_col}"}
        
        try:
            # 使用pandas创建透视表
            pivot_result = pd.pivot_table(
                df,
                values=actual_value_col,
                index=actual_index_col,
                columns=actual_column_col,
                aggfunc=agg_func,
                fill_value=0  # 用0填充空值
            )
            
            # 将结果转换为字典格式
            result = {}
            result["透视表"] = {str(k): v.to_dict() for k, v in pivot_result.items()}
            
            return result
        except Exception as e:
            return {"error": f"透视表操作失败: {str(e)}"}
    else:
        return {"error": "透视表操作需要指定行、列和值的字典格式"}
