# -*- coding: utf-8 -*-
"""
数据处理器模块
用于执行具体的Python计算任务
"""

import pandas as pd
import numpy as np
from io import StringIO

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
                        data_lines = [line.split('\t') for line in lines[1:]]
                        df = pd.DataFrame(data_lines, columns=headers)
                    elif ',' in first_line:
                        # 处理逗号分隔的文件
                        headers = first_line.split(',')
                        data_lines = [line.split(',') for line in lines[1:]]
                        df = pd.DataFrame(data_lines, columns=headers)
                    elif '|' in first_line:
                        # 处理管道符分隔的文件
                        headers = first_line.split('|')
                        data_lines = [line.split('|') for line in lines[1:]]
                        df = pd.DataFrame(data_lines, columns=headers)
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
                if column in df.columns:
                    actual_column = column
                else:
                    # 尝试模糊匹配
                    for col in df.columns:
                        if column in col or col in column:
                            actual_column = col
                            break
            
            if column and not actual_column:
                results[f"{op_name}_{column}"] = f"错误：列 '{column}' 不存在"
                continue
                
            if op_name == "mean":
                if actual_column:
                    results[f"{column}_平均值"] = float(df[actual_column].mean())
                else:
                    # 对所有数值列计算平均值
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        results[f"{col}_平均值"] = float(df[col].mean())
                        
            elif op_name == "sum":
                if actual_column:
                    results[f"{column}_总和"] = float(df[actual_column].sum())
                else:
                    # 对所有数值列计算总和
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        results[f"{col}_总和"] = float(df[col].sum())
                        
            elif op_name == "max":
                if actual_column:
                    results[f"{column}_最大值"] = float(df[actual_column].max())
                else:
                    # 对所有数值列计算最大值
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        results[f"{col}_最大值"] = float(df[col].max())
                        
            elif op_name == "min":
                if actual_column:
                    results[f"{column}_最小值"] = float(df[actual_column].min())
                else:
                    # 对所有数值列计算最小值
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        results[f"{col}_最小值"] = float(df[col].min())
                        
            elif op_name == "count":
                if actual_column:
                    results[f"{column}_计数"] = int(df[actual_column].count())
                else:
                    # 对所有列计算计数
                    for col in df.columns:
                        results[f"{col}_计数"] = int(df[col].count())
                        
            elif op_name == "std":
                if actual_column:
                    results[f"{column}_标准差"] = float(df[actual_column].std())
                else:
                    # 对所有数值列计算标准差
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        results[f"{col}_标准差"] = float(df[col].std())
                        
            elif op_name == "unique":
                if actual_column:
                    unique_values = df[actual_column].unique().tolist()
                    results[f"{column}_唯一值"] = unique_values
                else:
                    # 对所有列计算唯一值
                    for col in df.columns:
                        unique_values = df[col].unique().tolist()
                        results[f"{col}_唯一值"] = unique_values
                        
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
