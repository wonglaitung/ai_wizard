# -*- coding: utf-8 -*-
"""
数据处理器模块
用于执行具体的Python计算任务
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

def process_data(task_plan, file_content=None):
    """
    根据任务计划执行数据处理
    
    Args:
        task_plan (dict): 任务计划
        file_content (str): 文件内容
        
    Returns:
        dict: 计算结果
    """
    
    # 如果没有文件内容，创建示例数据
    if not file_content:
        # 创建示例数据
        data = {
            '日期': pd.date_range('2023-01-01', periods=12, freq='M'),
            '销售额': [1000, 1200, 1100, 1300, 1250, 1400, 1500, 1450, 1600, 1550, 1700, 1800],
            '成本': [600, 700, 650, 750, 720, 800, 850, 820, 900, 880, 950, 1000],
            '利润': [400, 500, 450, 550, 530, 600, 650, 630, 700, 670, 750, 800]
        }
        df = pd.DataFrame(data)
    else:
        # 尝试解析文件内容为DataFrame
        try:
            # 假设是CSV格式
            df = pd.read_csv(StringIO(file_content))
        except:
            try:
                # 如果不是CSV，尝试作为文本处理
                lines = file_content.strip().split('\n')
                if len(lines) > 1:
                    # 检查是否是制表符分隔的文件
                    first_line = lines[0]
                    if '\t' in first_line:
                        # 处理制表符分隔的文件
                        headers = first_line.split('\t')
                        # 清理列名中的多余空格
                        headers = [header.strip() for header in headers]
                        data_lines = [line.split('\t') for line in lines[1:]]
                        # 清理数据行中的多余空格
                        cleaned_data_lines = []
                        for line in data_lines:
                            cleaned_line = [item.strip() for item in line]
                            cleaned_data_lines.append(cleaned_line)
                        df = pd.DataFrame(cleaned_data_lines, columns=headers)
                    elif ',' in first_line:
                        # 处理逗号分隔的文件
                        headers = first_line.split(',')
                        # 清理列名中的多余空格
                        headers = [header.strip() for header in headers]
                        data_lines = [line.split(',') for line in lines[1:]]
                        # 清理数据行中的多余空格
                        cleaned_data_lines = []
                        for line in data_lines:
                            cleaned_line = [item.strip() for item in line]
                            cleaned_data_lines.append(cleaned_line)
                        df = pd.DataFrame(cleaned_data_lines, columns=headers)
                    elif '|' in first_line:
                        # 处理管道符分隔的文件
                        headers = first_line.split('|')
                        # 清理列名中的多余空格
                        headers = [header.strip() for header in headers]
                        data_lines = [line.split('|') for line in lines[1:]]
                        # 清理数据行中的多余空格
                        cleaned_data_lines = []
                        for line in data_lines:
                            cleaned_line = [item.strip() for item in line]
                            cleaned_data_lines.append(cleaned_line)
                        df = pd.DataFrame(cleaned_data_lines, columns=headers)
                    else:
                        # 如果没有明显的分隔符，尝试根据空格分割，但保留原始列名
                        # 这里处理复杂的情况，如列名里包含多个信息
                        # 清理列名中的多余空格
                        cleaned_first_line = ' '.join(first_line.split())
                        headers = [cleaned_first_line]
                        data_lines = [[line.strip()] for line in lines[1:]]
                        df = pd.DataFrame(data_lines, columns=headers)
                        
                        # 进一步处理列名，尝试提取实际的列名
                        if len(headers) == 1 and ' ' in headers[0]:
                            # 如果列名中包含空格，尝试提取有意义的部分
                            original_column = headers[0]
                            # 移除多余的空格
                            cleaned_column = ' '.join(original_column.split())
                            df.columns = [cleaned_column]
                else:
                    # 只有一行数据
                    df = pd.DataFrame([file_content.split(',')])
            except Exception as e:
                # 如果都失败了，返回错误
                return {
                    "error": f"无法解析文件内容: {str(e)}",
                    "results": {}
                }
    
    # 清理所有列名中的多余空格
    df.columns = [col.strip() for col in df.columns]
    
    # 执行计算任务
    results = {}
    
    # 如果指定了列，只处理这些列
    columns = task_plan.get("columns", [])
    if columns:
        # 只保留指定的列
        existing_columns = [col for col in columns if col in df.columns]
        # 如果没有完全匹配的列，尝试模糊匹配
        if not existing_columns:
            for col in columns:
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
            
            # 尝试匹配列名
            actual_column = None
            if column:
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
            
            if column and not actual_column:
                results[f"{op_name}_{column}"] = f"错误：列 '{column}' 不存在"
                continue
                
            # 使用注册的操作处理函数
            if op_name in OPERATION_REGISTRY:
                operation_func = OPERATION_REGISTRY[op_name]
                operation_result = operation_func(df, actual_column if actual_column else df.columns.tolist())
                
                # 根据操作结果更新results字典
                if actual_column:
                    # 如果指定了具体列，则添加列名前缀
                    if isinstance(operation_result, dict):
                        results[f"{column}_"] = operation_result
                    else:
                        results[f"{column}_{op_name}"] = operation_result
                else:
                    # 如果没有指定列，则对所有列应用操作
                    if isinstance(operation_result, dict):
                        results.update(operation_result)
                    else:
                        # 如果返回单个值，对所有列进行处理
                        for col in df.columns:
                            results[f"{col}_{op_name}"] = operation_result
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
    计算平均值操作
    
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
            result[f"{col}_平均值"] = float(df[col].mean())
        return result
    else:
        # 对指定列计算平均值
        return float(df[columns].mean())


@register_operation("sum")
def sum_operation(df, columns):
    """
    计算总和操作
    
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
            result[f"{col}_总和"] = float(df[col].sum())
        return result
    else:
        # 对指定列计算总和
        return float(df[columns].sum())


@register_operation("max")
def max_operation(df, columns):
    """
    计算最大值操作
    
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
            result[f"{col}_最大值"] = float(df[col].max())
        return result
    else:
        # 对指定列计算最大值
        return float(df[columns].max())


@register_operation("min")
def min_operation(df, columns):
    """
    计算最小值操作
    
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
            result[f"{col}_最小值"] = float(df[col].min())
        return result
    else:
        # 对指定列计算最小值
        return float(df[columns].min())


@register_operation("count")
def count_operation(df, columns):
    """
    计算计数操作
    
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
            result[f"{col}_计数"] = int(df[col].count())
        return result
    else:
        # 对指定列计算计数
        return int(df[columns].count())


@register_operation("percentage")
def percentage_operation(df, columns):
    """
    计算百分比操作
    
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
    计算标准差操作
    
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
            result[f"{col}_标准差"] = float(df[col].std())
        return result
    else:
        # 对指定列计算标准差
        return float(df[columns].std())


@register_operation("unique")
def unique_operation(df, columns):
    """
    计算唯一值操作
    
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
    计算中位数操作
    
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
            result[f"{col}_中位数"] = float(df[col].median())
        return result
    else:
        # 对指定列计算中位数
        return float(df[columns].median())


@register_operation("mode")
def mode_operation(df, columns):
    """
    计算众数操作
    
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
    计算方差操作
    
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
            result[f"{col}_方差"] = float(df[col].var())
        return result
    else:
        # 对指定列计算方差
        return float(df[columns].var())


@register_operation("quantile_25")
def quantile_25_operation(df, columns):
    """
    计算25%分位数操作
    
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
            result[f"{col}_25分位数"] = float(df[col].quantile(0.25))
        return result
    else:
        # 对指定列计算25%分位数
        return float(df[columns].quantile(0.25))


@register_operation("quantile_75")
def quantile_75_operation(df, columns):
    """
    计算75%分位数操作
    
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
            result[f"{col}_75分位数"] = float(df[col].quantile(0.75))
        return result
    else:
        # 对指定列计算75%分位数
        return float(df[columns].quantile(0.75))


@register_operation("range")
def range_operation(df, columns):
    """
    计算数值范围（最大值-最小值）操作
    
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
            data_range = float(df[col].max()) - float(df[col].min())
            result[f"{col}_范围"] = data_range
        return result
    else:
        # 对指定列计算范围
        data_range = float(df[columns].max()) - float(df[columns].min())
        return data_range


@register_operation("first")
def first_operation(df, columns):
    """
    获取第一行数据操作
    
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
    获取最后一行数据操作
    
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
    计算缺失值数量操作
    
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
    计算缺失值百分比操作
    
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
    计算数值列之间的相关性矩阵操作
    
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
