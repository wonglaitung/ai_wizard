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
import ast
import operator
from typing import Dict, Any, Optional, Union
from llm_services.qwen_engine import chat_with_llm

# 配置日志
logger = logging.getLogger(__name__)

class DynamicCodeExecutor:
    """动态代码执行器，用于安全执行大模型生成的代码"""
    
    def __init__(self):
        # 定义安全操作的白名单
        self.safe_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
        }
        
        # 定义安全函数的白名单
        self.safe_funcs = {
            'abs', 'round', 'min', 'max', 'sum', 'len', 'range', 'enumerate', 
            'zip', 'map', 'filter', 'list', 'dict', 'set', 'tuple', 'str', 'int', 'float',
            'bool', 'complex', 'frozenset', 'ord', 'chr', 'hex', 'oct', 'pow', 'divmod'
        }
    
    def execute_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        在安全环境中执行代码
        """
        try:
            # 清理生成的代码，移除注释和import语句
            cleaned_code = self._clean_generated_code(code)
            
            # 检查清理后的代码是否包含多行
            lines = [line.strip() for line in cleaned_code.split('\n') if line.strip()]
            
            if len(lines) > 1:
                # 如果是多行代码，需要特殊处理
                # 创建一个临时变量来捕获最终结果
                result_var = "__result__"
                
                # 检查最后一行是否是不完整的（如被截断的代码）
                last_line = lines[-1]
                
                # 尝试构建完整的代码
                try:
                    # 尝试解析完整的代码块
                    code_with_result = "\n".join(lines[:-1]) + f"\n{result_var} = {last_line}"
                    tree = ast.parse(code_with_result)
                    
                    # 验证AST的安全性
                    if not self._is_safe_ast(tree):
                        return {"error": "代码包含不安全的操作", "success": False}
                    
                    # 创建安全的执行环境
                    safe_namespaces = {
                        "__builtins__": {name: __builtins__[name] for name in self.safe_funcs if name in __builtins__},
                        'pd': pd,
                        'np': np,
                        'df': df,
                        # 添加临时变量
                        result_var: None
                    }
                    
                    # 执行代码
                    exec(compile(tree, '<generated>', 'exec'), safe_namespaces)
                    
                    # 获取结果
                    result = safe_namespaces.get(result_var)
                except SyntaxError:
                    # 如果完整代码解析失败，尝试仅执行前面的行并返回最后一行作为表达式
                    if len(lines) > 1:
                        # 尝试执行前面的行
                        exec_code = "\n".join(lines[:-1])
                        try:
                            exec_tree = ast.parse(exec_code)
                            
                            if not self._is_safe_ast(exec_tree):
                                return {"error": "代码包含不安全的操作", "success": False}
                            
                            safe_namespaces = {
                                "__builtins__": {name: __builtins__[name] for name in self.safe_funcs if name in __builtins__},
                                'pd': pd,
                                'np': np,
                                'df': df,
                                # 添加临时变量
                                result_var: None
                            }
                            
                            exec(compile(exec_tree, '<generated>', 'exec'), safe_namespaces)
                            
                            # 对最后一行使用eval
                            eval_code = lines[-1].strip()
                            if eval_code:
                                # 检查代码是否包含可能导致"The truth value of a DataFrame is ambiguous"错误的直接布尔比较
                                # 区分条件表达式（三元运算符，包含 'if ... else'）和布尔判断（仅包含 'if'）
                                if ('if ' in eval_code and ' else ' not in eval_code) or ' and ' in eval_code or ' or ' in eval_code or ('==' in eval_code and 'df' in eval_code) or ('!=' in eval_code and 'df' in eval_code):
                                    # 这种情况下不能直接使用eval，需要使用exec（这是布尔判断，不是条件表达式）
                                    # 创建一个新的临时变量来保存结果
                                    temp_result_var = "__temp_result__"
                                    # 尝试构建一个安全的执行环境
                                    exec_code_for_bool = f"try:\n    {temp_result_var} = {eval_code}\nexcept ValueError as e:\n    if 'The truth value of a DataFrame is ambiguous' in str(e):\n        {temp_result_var} = 'Boolean operation on DataFrame not allowed'\n    else:\n        raise e\nexcept Exception as e:\n    {temp_result_var} = f'Error: {{str(e)}}'"
                                    
                                    try:
                                        exec_tree = ast.parse(exec_code_for_bool, mode='exec')
                                        if self._is_safe_ast(exec_tree):
                                            exec(compile(exec_tree, '<generated>', 'exec'), safe_namespaces)
                                            result = safe_namespaces.get(temp_result_var)
                                            if isinstance(result, str) and result.startswith('Boolean operation on DataFrame not allowed'):
                                                return {"error": "Boolean operation on DataFrame not allowed - use .any(), .all(), .empty(), etc. instead", "success": False}
                                            elif isinstance(result, str) and result.startswith('Error:'):
                                                return {"error": f"代码执行错误: {result}", "success": False}
                                        else:
                                            return {"error": "代码包含不安全的操作", "success": False}
                                    except:
                                        return {"error": f"代码无法安全执行: {eval_code}", "success": False}
                                else:
                                    # 检查是否是条件表达式（三元运算符），这种情况下可以使用eval
                                    if 'if ' in eval_code and ' else ' in eval_code:
                                        # 这是条件表达式（三元运算符），可以使用eval
                                        eval_tree = ast.parse(eval_code, mode='eval')
                                        
                                        if not self._is_safe_ast(eval_tree):
                                            return {"error": "代码包含不安全的操作", "success": False}
                                        
                                        result = eval(compile(eval_tree, '<generated>', 'eval'), safe_namespaces)
                                    elif ('{' in eval_code or '}' in eval_code) and ('.agg(' in eval_code or '.groupby(' in eval_code):
                                        # 这可能是不完整的复杂表达式，尝试补全或简化
                                        simplified_eval_code = eval_code
                                        # 例如：将 df.groupby('col').agg({'A': 'sum',... 补全为完整表达式
                                        if simplified_eval_code.count('{') > simplified_eval_code.count('}'):
                                            # 添加缺失的右大括号
                                            simplified_eval_code += '}'
                                        
                                        try:
                                            eval_tree = ast.parse(simplified_eval_code, mode='eval')
                                            
                                            if not self._is_safe_ast(eval_tree):
                                                return {"error": "代码包含不安全的操作", "success": False}
                                            
                                            result = eval(compile(eval_tree, '<generated>', 'eval'), safe_namespaces)
                                        except:
                                            # 如果还是失败，使用原代码进行最后尝试
                                            try:
                                                eval_tree = ast.parse(eval_code, mode='eval')
                                                
                                                if not self._is_safe_ast(eval_tree):
                                                    return {"error": "代码包含不安全的操作", "success": False}
                                                
                                                result = eval(compile(eval_tree, '<generated>', 'eval'), safe_namespaces)
                                            except:
                                                # 所有尝试都失败了
                                                return {"error": f"代码语法错误: {eval_code}", "success": False}
                                    else:
                                        eval_tree = ast.parse(eval_code, mode='eval')
                                        
                                        if not self._is_safe_ast(eval_tree):
                                            return {"error": "代码包含不安全的操作", "success": False}
                                        
                                        result = eval(compile(eval_tree, '<generated>', 'eval'), safe_namespaces)
                            else:
                                result = safe_namespaces.get(result_var)
                        except SyntaxError:
                            # 如果前面的行也无法解析，尝试将所有代码作为表达式解析（用于处理不完整/截断的代码）
                            # 先尝试原始的完整代码
                            full_code_to_try = "\n".join(lines)
                            try:
                                eval_tree = ast.parse(full_code_to_try, mode='eval')
                                
                                if self._is_safe_ast(eval_tree):
                                    safe_namespaces = {
                                        "__builtins__": {name: __builtins__[name] for name in self.safe_funcs if name in __builtins__},
                                        'pd': pd,
                                        'np': np,
                                        'df': df
                                    }
                                    
                                    result = eval(compile(eval_tree, '<generated>', 'eval'), safe_namespaces)
                                else:
                                    return {"error": "代码包含不安全的操作", "success": False}
                            except:
                                # 尝试找到一个有效的表达式子集，从较短的子集开始
                                for i in range(len(lines), 0, -1):
                                    try:
                                        partial_code = "\n".join(lines[:i]).strip()
                                        if partial_code and not partial_code.endswith(',') and not partial_code.endswith(':') and not partial_code.endswith('{'):
                                            eval_tree = ast.parse(partial_code, mode='eval')
                                            
                                            if not self._is_safe_ast(eval_tree):
                                                continue  # 继续尝试更短的代码
                                            
                                            safe_namespaces = {
                                                "__builtins__": {name: __builtins__[name] for name in self.safe_funcs if name in __builtins__},
                                                'pd': pd,
                                                'np': np,
                                                'df': df
                                            }
                                            
                                            result = eval(compile(eval_tree, '<generated>', 'eval'), safe_namespaces)
                                            break
                                    except:
                                        continue
                                else:
                                    # 如果所有子集都失败了
                                    return {"error": f"代码语法错误", "success": False}
                    else:
                        # 只有一行代码，但解析失败
                        return {"error": f"代码语法错误", "success": False}
            else:
                # 单个表达式，使用eval
                if not cleaned_code.strip():
                    return {"result": None, "success": True}
                
                tree = ast.parse(cleaned_code.strip(), mode='eval')
                
                # 验证AST的安全性
                if not self._is_safe_ast(tree):
                    return {"error": "代码包含不安全的操作", "success": False}
                
                # 创建安全的执行环境
                safe_namespaces = {
                    "__builtins__": {name: __builtins__[name] for name in self.safe_funcs if name in __builtins__},
                    'pd': pd,
                    'np': np,
                    'df': df
                }
                
                # 执行代码
                result = eval(compile(tree, '<generated>', 'eval'), safe_namespaces)
            
            return {"result": result, "success": True}
        except SyntaxError as se:
            # 语法错误，可能因为代码太复杂或包含不兼容的语法
            logger.error(f"代码语法错误: {str(se)}")
            return {"error": f"代码语法错误: {str(se)}", "success": False}
        except Exception as e:
            logger.error(f"执行生成的代码时出错: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _clean_generated_code(self, code: str) -> str:
        """
        清理大模型生成的代码，移除注释和import语句，并处理已弃用的方法
        """
        # 按行分割代码
        lines = code.strip().split('\n')
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
            
            # 将Series.append()方法调用转换为pd.concat()，因为append在新版本pandas中已被弃用
            import re
            # 处理各种情况，如 df.append(...)、df['col'].append(...)、df.method().append(...)、df['col'].dropna().append(...) 等
            # 使用更精确的正则表达式来匹配对象的append方法调用
            # 匹配任何可能的链式调用后跟.append()的部分
            line = re.sub(r'([a-zA-Z0-9_][a-zA-Z0-9_\[\]\'"\\.\s\(\)]+)\.append\(\s*([^)]+?)\s*\)', r'pd.concat([\1, \2], ignore_index=True)', line)
            
            cleaned_lines.append(line)
        
        # 重新组合代码
        cleaned_code = '\n'.join(cleaned_lines)
        return cleaned_code
    
    def _is_safe_ast(self, tree: ast.AST) -> bool:
        """
        检查AST是否包含安全的操作
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # 检查函数调用是否安全
                if isinstance(node.func, ast.Name):
                    # 直接函数调用，如 sum(df['A']), __import__('os') 等
                    if node.func.id not in self.safe_funcs:
                        # 如果不是安全函数，检查是否是变量名（如df.sum()中的df）或安全的变量
                        if node.func.id not in ['df', '__result__', '__temp_result__']:  # 允许__result__和__temp_result__变量
                            return False
                elif isinstance(node.func, ast.Attribute):
                    # 方法调用，如 df['A'].sum(), df.groupby() 等
                    # 或pandas函数调用，如 pd.crosstab, pd.concat等
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'pd':
                        # 这是pd.开头的函数调用，检查是否为允许的pandas函数
                        allowed_pd_funcs = {'crosstab', 'concat', 'merge', 'pivot_table', 'get_dummies', 'cut', 'qcut', 'melt', 'date_range', 'to_datetime', 'Series', 'DataFrame'}
                        if node.func.attr not in allowed_pd_funcs:
                            return False
                    # 递归检查属性值是否安全
                    elif not self._is_safe_attr_chain(node.func):
                        return False
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                # 禁止导入语句
                return False
            elif isinstance(node, ast.Assign):
                # 检查赋值语句是否安全 - 只允许赋值给特定变量
                if isinstance(node.targets[0], ast.Name):
                    if node.targets[0].id not in ['__result__']:  # 只允许给__result__变量赋值
                        return False
            elif isinstance(node, ast.AugAssign):
                # 禁止增强赋值语句
                return False
            elif isinstance(node, ast.For):
                # 禁止for循环（可能耗时过长）
                return False
            elif isinstance(node, ast.While):
                # 禁止while循环（可能耗时过长）
                return False
            elif isinstance(node, ast.FunctionDef):
                # 禁止函数定义
                return False
            elif isinstance(node, ast.ClassDef):
                # 禁止类定义
                return False
            elif isinstance(node, ast.Name):
                # 变量名必须是安全的
                if node.id not in ['df', 'pd', 'np', '__result__'] + list(self.safe_funcs):  # 允许__result__变量
                    return False
            elif type(node).__name__ not in ['Expression', 'Str', 'Num', 'Constant', 'Name', 'BinOp', 'UnaryOp', 
                                           'Compare', 'BoolOp', 'List', 'Tuple', 'Dict', 'Subscript', 
                                           'Attribute', 'Call', 'Index', 'Slice', 'ExtSlice', 'Load', 'Store', 'Del',
                                           'Module', 'Expr', 'Assign', 'keyword', 'Starred', 'comprehension', 'ListComp',
                                           'GeneratorExp', 'SetComp', 'DictComp', 'IfExp', 'Lambda', 'arguments', 'arg',
                                           'Tuple', 'Ellipsis', 'Pass', 'Break', 'Continue', 'Add', 'Mult', 'Sub', 'Div',
                                           'Mod', 'Pow', 'LShift', 'RShift', 'BitOr', 'BitXor', 'BitAnd', 'FloorDiv']:  # 扩展节点类型白名单
                # 其他未明确允许的节点类型认为是不安全的
                # Load, Store, Del 是访问上下文节点，是安全的
                return False
        return True

    def _is_safe_attr_chain(self, node):
        """
        检查属性访问链是否安全（例如 df['A'].sum()）
        """
        if isinstance(node, ast.Attribute):
            # 检查属性值（如 df['A'] 部分）和属性名（如 sum）
            attr_name = node.attr
            # 允许pandas和numpy的常用方法
            allowed_attrs = {
                'sum', 'mean', 'max', 'min', 'count', 'std', 'var', 'median', 'mode',
                'quantile', 'abs', 'round', 'dropna', 'fillna', 'unique', 'tolist',
                'groupby', 'agg', 'merge', 'concat', 'append', 'sort_values', 'reset_index',
                'pivot_table', 'crosstab', 'corr', 'cov', 'describe', 'head', 'tail',
                'loc', 'iloc', 'assign', 'rename', 'replace', 'apply', 'map', 'any', 'all', 'empty', 'bool', 'item',
                'isna', 'notna', 'fillna', 'ffill', 'bfill', 'interpolate', 'values', 'index', 'columns', 'dtypes',
                'shape', 'size', 'nunique', 'value_counts', 'sample', 'drop_duplicates', 'duplicated', 'shift',
                'rolling', 'expanding', 'ewm', 'std', 'sem', 'mad', 'mad', 'skew', 'kurt', 'cumsum', 'cummax',
                'cummin', 'cumprod', 'diff', 'pct_change', 'add', 'sub', 'mul', 'div', 'mod', 'pow',
                'get_group', 'size', 'first', 'last', 'nth', 'head', 'tail', 'cumcount', 'ngroup', 'groups',
                'transform', 'filter', 'std', 'var', 'sem', 'count', 'nunique', 'idxmax', 'idxmin',
                'fillna', 'dropna', 'ffill', 'bfill', 'interpolate', 'rank', 'quantile', 'corrwith',
                'to_frame', 'to_list', 'to_dict', 'to_numpy', 'squeeze', 'copy', 'clip', 'round', 'swaplevel',
                'isin', 'between', 'isna', 'notna', 'isnull', 'notnull', 'duplicated', 'drop_duplicates',
                'value_counts', 'sample', 'nlargest', 'nsmallest', 'idxmax', 'idxmin', 'align',
                'update', 'join', 'combine', 'combine_first', 'where', 'mask', 'query', 'eval', 'pipe',
                'agg', 'aggregate', 'apply', 'transform'
            }
            if attr_name not in allowed_attrs:
                return False
            # 检查属性值（如 df['A'] 部分）
            return self._is_safe_attr_value(node.value)
        else:
            return False

    def _is_safe_attr_value(self, node):
        """
        检查属性值是否安全
        """
        if isinstance(node, ast.Name):
            # 如 df
            return node.id in ['df', 'pd', 'np']
        elif isinstance(node, ast.Subscript):
            # 如 df['A']
            return isinstance(node.value, ast.Name) and node.value.id == 'df'
        elif isinstance(node, ast.Attribute):
            # 如链式调用 df.groupby('A')
            return self._is_safe_attr_chain(node)
        else:
            # 其他类型如Call是不安全的，因为可能是 __import__('os').system()
            return False


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
                        # 如果没有管道符，尝试使用空格分隔
                        df = pd.read_csv(StringIO(df_str), sep='\s+', engine='python')
                    parsed_dataframes[current_sheet_name] = df
                except Exception as e:
                    # 如果解析失败，尝试其他方法
                    try:
                        # 再次检查是否包含管道符
                        df_str = '\n'.join(sheet_data)
                        if '|' in df_str:
                            df = pd.read_csv(StringIO(df_str), sep='|')
                        else:
                            df = pd.read_csv(StringIO(df_str))
                        parsed_dataframes[current_sheet_name] = df
                    except Exception as e2:
                        logger.error(f"无法解析工作表 {current_sheet_name} 的数据: {e}, {e2}")
                        
            # 开始新工作表 - handle both Chinese and English formats
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
            # 检查数据中是否包含管道符，优先使用管道符分隔
            if '|' in df_str:
                df = pd.read_csv(StringIO(df_str), sep='|')
            else:
                df = pd.read_csv(StringIO(df_str), sep='\s+', engine='python')
            parsed_dataframes[current_sheet_name] = df
        except:
            try:
                # 再次检查是否包含管道符
                df_str = '\n'.join(sheet_data)
                if '|' in df_str:
                    df = pd.read_csv(StringIO(df_str), sep='|')
                else:
                    df = pd.read_csv(StringIO(df_str))
                parsed_dataframes[current_sheet_name] = df
            except:
                logger.error(f"无法解析工作表 {current_sheet_name} 的数据")
    
    return parsed_dataframes


class DataProcessor:
    """数据处理器，完全依赖大模型在线生成代码"""
    
    def __init__(self, api_key: str, settings: Optional[Dict] = None):
        self.api_key = api_key
        self.settings = settings or {}
        self.executor = DynamicCodeExecutor()
    
    def process_data(self, task_plan: Dict[str, Any], file_content: Optional[str] = None) -> Dict[str, Any]:
        """
        根据任务计划执行数据处理，完全依赖大模型生成代码
        """
        # 解析数据
        df, multi_sheet_data = self._parse_data(file_content)
        
        results = {}
        
        # 获取操作列表
        operations = task_plan.get("operations", [])
        
        # 如果是多工作表数据，需要特殊处理
        if multi_sheet_data:
            # 对于需要合并工作表数据的操作（如交叉分析），创建合并的数据集
            all_dfs = []
            
            # 分析所有工作表，将它们按行合并，并添加工作表来源标识
            for sheet_name, sheet_df in multi_sheet_data.items():
                # 重命名列以区分不同工作表的同类数据
                renamed_df = sheet_df.copy()
                
                # Standardize column names to ensure consistent semantic meaning
                new_columns = {}
                for col in renamed_df.columns:
                    # Generic logic to handle similar columns across sheets
                    # Look for potential duplicates and add sheet identifier
                    duplicate_found = False
                    for other_sheet_name, other_sheet_df in multi_sheet_data.items():
                        if other_sheet_name != sheet_name:
                            for other_col in other_sheet_df.columns:
                                # Check if columns are semantically similar
                                if (col == other_col or 
                                    col.replace(" ", "").replace("_", "").lower() == other_col.replace(" ", "").replace("_", "").lower() or 
                                    col in other_col or other_col in col or
                                    # 新增：检查是否是相同语义但不同时间点的列（通用处理，不限定特定月份）
                                    (col.replace("月", "").replace("末", "").replace("初", "").replace("上", "").replace("下", "") == 
                                     other_col.replace("月", "").replace("末", "").replace("初", "").replace("上", "").replace("下", ""))):
                                    duplicate_found = True
                                    break
                            if duplicate_found:
                                break
                    
                    if duplicate_found:
                        # Add sheet name as suffix to distinguish between sheets
                        new_columns[col] = f"{col}_{sheet_name}"
                    else:
                        # Keep original name if not duplicated
                        new_columns[col] = col
                
                renamed_df = renamed_df.rename(columns=new_columns)
                renamed_df['_source_sheet'] = sheet_name  # 添加来源工作表标识
                all_dfs.append(renamed_df)
            
            # 合并所有工作表的数据
            if all_dfs:
                try:
                    # 按行合并所有工作表的数据，使用外连接保留所有列
                    df = pd.concat(all_dfs, ignore_index=True, sort=False)
                except Exception as e:
                    logger.warning(f"合并工作表数据时出错，使用第一个工作表: {str(e)}")
                    df = list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()
            else:
                df = list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()
            
            # 对于特定工作表的操作，需要映射到实际的重命名列
            processed_operations = []
            for op in operations:
                op_column = op.get("column")
                if op_column and "." in op_column:
                    # 分离工作表名和列名
                    parts = op_column.split(".", 1)
                    sheet_name, column_name = parts[0], parts[1]
                    
                    # 查找实际的重命名列 - 尝试匹配 "列名_工作表名" 格式
                    actual_column = None
                    for col in df.columns:
                        # 检查是否为 "列名_工作表名" 格式
                        if col == f"{column_name}_{sheet_name}" or col.startswith(f"{column_name}_{sheet_name}"):
                            actual_column = col
                            break
                    
                    if actual_column:
                        # 创建新操作，使用实际的列名
                        new_op = op.copy()  # 使用浅拷贝
                        new_op["column"] = actual_column
                        processed_operations.append(new_op)
                    else:
                        # 如果没找到匹配的列，保留原操作，让后续逻辑处理错误
                        processed_operations.append(op)
                else:
                    processed_operations.append(op)
            
            # 处理每个操作
            for op in processed_operations:
                try:
                    op_name = op.get("name")
                    column = op.get("column")
                    sheet_name = op.get("_sheet")  # 获取指定的工作表（这个是在列映射前设置的）
                    
                    # 使用合并后的数据框进行操作（所有数据都在一个DataFrame中）
                    current_df = df  # 使用合并后的df，而不是特定工作表的df
                    
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
                        
                        # 如果还是没找到，尝试更智能的匹配逻辑，特别是处理工作表特定的列名
                        if not actual_column:
                            # 检查是否是类似"1月末客户编码清单"但实际在数据中是"1月末客户编码清单_Sheet2"的列
                            for col in current_df.columns:
                                # 检查列名是否包含原始列名，或原始列名是否包含在列名中
                                if (stripped_column in col or col in stripped_column or
                                    # 特殊处理：检查是否是相同语义但带工作表后缀的列
                                    col.startswith(f"{stripped_column}_") or 
                                    col.endswith(f"_{stripped_column}")):
                                    actual_column = col
                                    break
                    
                    # 特别处理 "SheetN.列名" 格式的列引用 - 如果上面没找到，尝试在合并数据中查找对应的重命名列
                    if not actual_column and column and isinstance(column, str) and "." in column:
                        parts = column.split(".", 1)
                        if len(parts) == 2:
                            sheet_part, col_part = parts[0], parts[1]
                            # 查找 "列名_工作表名" 格式的实际列
                            for col in current_df.columns:
                                if col == f"{col_part}_{sheet_part}" or col.startswith(f"{col_part}_{sheet_part}"):
                                    actual_column = col
                                    break
                    
                    if column and not actual_column and isinstance(column, str):
                        column_ref = f"{sheet_name}.{column}" if sheet_name else column
                        results[f"{op_name}_{column_ref}"] = f"错误：列 '{column_ref}' 不存在，可用的列: {list(current_df.columns)}"
                        continue
                        
                    # 直接使用大模型生成代码执行操作
                    try:
                        generated_code = self._generate_operation_code(task_plan, op, current_df)
                        execution_result = self.executor.execute_code(generated_code, current_df)
                        
                        if execution_result["success"]:
                            column_ref = actual_column if actual_column and not isinstance(column, (dict, list)) else (f"{sheet_name}.{column}" if sheet_name and column else (column or "all"))
                            if actual_column and not isinstance(column, (dict, list)):
                                results[f"{actual_column}_{op_name}_dynamic"] = self._convert_pandas_types(execution_result["result"])
                            else:
                                results[f"{op_name}_dynamic_result"] = self._convert_pandas_types(execution_result["result"])
                        else:
                            results[f"{op_name}_error"] = f"动态代码执行错误: {execution_result['error']}"
                    except Exception as e:
                        results[f"{op_name}_error"] = f"生成动态代码错误: {str(e)}"
                                
                except Exception as e:
                    column_ref = op.get("column", "unknown")
                    sheet_name = op.get("_sheet")
                    full_column_ref = f"{sheet_name}.{column_ref}" if sheet_name else column_ref
                    results[op.get("name", "unknown")] = f"计算错误: {str(e)} (列: {full_column_ref})"
        else:
            # 单工作表数据的处理逻辑
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
                        
                    # 直接使用大模型生成代码执行操作
                    try:
                        generated_code = self._generate_operation_code(task_plan, op, df)
                        execution_result = self.executor.execute_code(generated_code, df)
                        
                        if execution_result["success"]:
                            if actual_column and not isinstance(column, (dict, list)):
                                results[f"{actual_column}_{op_name}_dynamic"] = self._convert_pandas_types(execution_result["result"])
                            else:
                                results[f"{op_name}_dynamic_result"] = self._convert_pandas_types(execution_result["result"])
                        else:
                            results[f"{op_name}_error"] = f"动态代码执行错误: {execution_result['error']}"
                    except Exception as e:
                        results[f"{op_name}_error"] = f"生成动态代码错误: {str(e)}"
                                
                except Exception as e:
                    results[op_name] = f"计算错误: {str(e)}"
        
        # 确保返回转换后的结果
        return self._convert_pandas_types(results)
    
    
    def _convert_pandas_types(self, obj):
        """
        将pandas和numpy数据类型转换为Python原生类型以支持JSON序列化
        """
        import numpy as np
        import pandas as pd
        
        if isinstance(obj, dict):
            return {key: self._convert_pandas_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_pandas_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_pandas_types(item) for item in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):  # 检查pandas的NaN值
            return None
        elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
            return str(obj)
        elif isinstance(obj, np.ndarray):
            return self._convert_pandas_types(obj.tolist())
        elif isinstance(obj, pd.Series):
            return self._convert_pandas_types(obj.to_dict())
        elif isinstance(obj, pd.DataFrame):
            return self._convert_pandas_types(obj.to_dict())
        else:
            return obj

    def _generate_operation_code(self, task_plan: Dict[str, Any], operation: Dict[str, Any], df: pd.DataFrame) -> str:
        """
        使用大模型生成执行特定操作的代码
        """
        user_request = f"""
        你是一个pandas专家，基于以下任务计划和数据，生成对应的pandas代码：
        
        任务计划: {task_plan}
        操作: {operation}
        数据列: {list(df.columns)}
        数据类型: {df.dtypes.to_dict()}
        
        请生成直接可用的pandas代码，用于执行该操作。
        代码应该只包含计算逻辑，不要包含函数定义或其他装饰。
        代码应该返回操作的结果。
        可用的变量是df（DataFrame）。
        请确保代码安全、高效，并且结果格式为可以被Python eval()函数安全执行的表达式。
        """
        
        # 准备模型参数
        model_params = {
            'model': self.settings.get('modelName', 'qwen-max'),
            'temperature': 0.1,  # 低温度以确保代码准确性
            'max_tokens': 1024,
            'top_p': 0.8,
            'frequency_penalty': 0.5,
            'api_key': self.api_key,
            'base_url': self.settings.get('baseUrl', None),
        }
        
        try:
            # 调用大模型生成代码
            generated_code = chat_with_llm(user_request, **model_params)
            
            # 清理生成的代码，移除不必要的标记
            if "```python" in generated_code:
                start_idx = generated_code.find("```python") + len("```python")
                end_idx = generated_code.find("```", start_idx)
                if end_idx == -1:
                    end_idx = len(generated_code)
                generated_code = generated_code[start_idx:end_idx].strip()
            elif "```" in generated_code:
                start_idx = generated_code.find("```") + len("```")
                end_idx = generated_code.find("```", start_idx)
                if end_idx == -1:
                    end_idx = len(generated_code)
                generated_code = generated_code[start_idx:end_idx].strip()
            
            return generated_code
        except Exception as e:
            logger.error(f"生成操作代码时出错: {str(e)}")
            # 返回一个默认的错误操作
            return "None"
    
    def _parse_data(self, file_content: Optional[str]):
        """
        解析数据的辅助方法
        """
        # 如果没有文件内容，创建示例数据
        if not file_content:
            # 创建示例数据
            data = {
                '日期': pd.date_range('2023-01-01', periods=12, freq='M'),
                '销售額': [1000, 1200, 1100, 1300, 1250, 1400, 1500, 1450, 1600, 1550, 1700, 1800],
                '成本': [600, 700, 650, 750, 720, 800, 850, 820, 900, 880, 950, 1000],
                '利润': [400, 500, 450, 550, 530, 600, 650, 630, 700, 670, 750, 800]
            }
            df = pd.DataFrame(data)
            return df, None
        else:
            # 檢查是否是多工作表數據（包含"工作表: "或"Sheet: "標記）
            if "工作表: " in file_content or "Sheet: " in file_content:
                # 解析多工作表數據
                multi_sheet_data = parse_multi_sheet_data(file_content)
                # 使用第一個工作表作為默認數據框
                df = list(multi_sheet_data.values())[0] if multi_sheet_data else pd.DataFrame()
                return df, multi_sheet_data
            else:
                # 尝试解析文件内容为DataFrame
                df = None
                multi_sheet_data = None
                # 首先尝试作为CSV格式读取
                try:
                    df = pd.read_csv(StringIO(file_content))
                except:
                    pass
                    
                # 检查第一行是否包含管道符，如果是则优先使用管道符分隔
                if file_content and '|' in file_content.split('\n')[0]:
                    try:
                        # 强制使用管道符分隔
                        df = pd.read_csv(StringIO(file_content), sep='|')
                    except:
                        pass
                # 检查第一行是否包含制表符，如果是则使用制表符分隔
                elif file_content and '\t' in file_content.split('\n')[0]:
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
                        return pd.DataFrame(), None
                        
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
                
                return df, multi_sheet_data


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
    # 如果提供了API密钥和设置，则使用增强版数据处理器
    if api_key is not None and settings is not None:
        processor = DataProcessor(api_key, settings)
        return processor.process_data(task_plan, file_content)
    else:
        # 如果没有提供API密钥和设置，直接报错
        raise ValueError("必须提供API密钥和设置参数才能使用数据处理器")