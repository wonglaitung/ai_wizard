"""
测试工具管理器功能
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from llm_services.tool_manager import tool_manager

def test_tool_schema():
    """测试工具Schema"""
    print("=" * 50)
    print("测试工具Schema")
    print("=" * 50)
    
    tools_schema = tool_manager.get_tools_schema()
    print(f"已注册的工具数量: {len(tools_schema)}")
    print()
    
    for tool_schema in tools_schema:
        tool_info = tool_schema['function']
        print(f"工具名称: {tool_info['name']}")
        print(f"工具描述: {tool_info['description']}")
        print(f"参数定义: {tool_info['parameters']}")
        print()

def test_tool_execution():
    """测试工具执行（仅测试参数验证，不实际执行浏览器操作）"""
    print("=" * 50)
    print("测试工具执行")
    print("=" * 50)
    
    test_cases = [
        ("open_url", {"url": "https://github.com"}),
        ("search_web", {"query": "Python教程", "search_engine": "baidu"}),
        ("open_github", {"repo": "wonglaitung/ai_wizard"}),
        ("open_youtube", {"query": "机器学习"})
    ]
    
    for tool_name, parameters in test_cases:
        print(f"测试工具: {tool_name}")
        print(f"参数: {parameters}")
        
        try:
            # 注意：实际执行会打开浏览器，这里只测试参数验证
            execution_result = tool_manager.execute_tool(tool_name, parameters)
            if execution_result['success']:
                print(f"✅ 工具执行成功: {execution_result['result']}")
            else:
                print(f"❌ 工具执行失败: {execution_result['error']}")
        except Exception as e:
            print(f"❌ 工具执行异常: {str(e)}")
        print()

def test_all():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("开始测试工具管理器")
    print("=" * 50 + "\n")
    
    test_tool_schema()
    test_tool_execution()
    
    print("=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_all()