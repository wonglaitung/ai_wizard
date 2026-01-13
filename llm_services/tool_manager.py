"""
工具管理模块
用于管理和执行大模型可调用的工具
"""

import logging
from typing import Dict, Any, Callable, Optional, List
from functools import wraps


logger = logging.getLogger(__name__)


class ToolManager:
    """工具管理器，负责注册和执行工具"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        注册工具的装饰器
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（JSON Schema格式）
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 注册工具
            self.tools[name] = {
                'function': wrapper,
                'description': description,
                'parameters': parameters,
                'name': name
            }
            logger.info(f"工具已注册: {name} - {description}")
            return wrapper
        return decorator
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的Schema（用于传递给大模型）
        
        Returns:
            工具Schema列表
        """
        return [
            {
                'type': 'function',
                'function': {
                    'name': tool['name'],
                    'description': tool['description'],
                    'parameters': tool['parameters']
                }
            }
            for tool in self.tools.values()
        ]
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定的工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            执行结果
        """
        if tool_name not in self.tools:
            return {
                'success': False,
                'error': f'工具不存在: {tool_name}',
                'result': None
            }
        
        tool = self.tools[tool_name]
        try:
            logger.info(f"执行工具: {tool_name}，参数: {parameters}")
            result = tool['function'](**parameters)
            logger.info(f"工具执行成功: {tool_name}")
            return {
                'success': True,
                'error': None,
                'result': result
            }
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name}, 错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'result': None
            }


# 创建全局工具管理器实例
tool_manager = ToolManager()


# ============ 基础工具实现 ============

@tool_manager.register_tool(
    name='open_url',
    description='生成指定的URL链接。适用于用户想要访问特定网站或网页的情况。',
    parameters={
        'type': 'object',
        'properties': {
            'url': {
                'type': 'string',
                'description': '要打开的URL地址，例如：https://github.com'
            }
        },
        'required': ['url']
    }
)
def open_url(url: str) -> Dict[str, str]:
    """
    生成指定的URL链接
    
    Args:
        url: 要打开的URL地址
        
    Returns:
        包含URL和操作建议的字典
    """
    try:
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return {
            'url': url,
            'action': 'open',
            'message': f'已为您生成链接，点击即可访问: {url}'
        }
    except Exception as e:
        raise Exception(f"生成URL失败: {str(e)}")


@tool_manager.register_tool(
    name='search_web',
    description='生成搜索引擎搜索链接。适用于用户想要查找信息的情况。',
    parameters={
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': '搜索关键词'
            },
            'search_engine': {
                'type': 'string',
                'description': '搜索引擎（可选），默认为百度，支持：baidu, google, bing',
                'enum': ['baidu', 'google', 'bing']
            }
        },
        'required': ['query']
    }
)
def search_web(query: str, search_engine: str = 'baidu') -> Dict[str, str]:
    """
    生成搜索引擎搜索链接
    
    Args:
        query: 搜索关键词
        search_engine: 搜索引擎（baidu, google, bing）
        
    Returns:
        包含URL和操作建议的字典
    """
    try:
        # 根据搜索引擎构建搜索URL
        search_urls = {
            'baidu': f'https://www.baidu.com/s?wd={query}',
            'google': f'https://www.google.com/search?q={query}',
            'bing': f'https://www.bing.com/search?q={query}'
        }
        
        url = search_urls.get(search_engine, search_urls['baidu'])
        
        engine_name = {
            'baidu': '百度',
            'google': '谷歌',
            'bing': '必应'
        }.get(search_engine, '百度')
        
        return {
            'url': url,
            'action': 'open',
            'message': f'已为您生成{engine_name}搜索链接，点击即可搜索: {query}'
        }
    except Exception as e:
        raise Exception(f"生成搜索链接失败: {str(e)}")


@tool_manager.register_tool(
    name='open_github',
    description='生成GitHub网站或指定GitHub仓库的链接。适用于用户想要访问GitHub的情况。',
    parameters={
        'type': 'object',
        'properties': {
            'repo': {
                'type': 'string',
                'description': 'GitHub仓库路径（可选），例如：wonglaitung/ai_wizard。如果不提供，则打开GitHub首页。'
            }
        },
        'required': []
    }
)
def open_github(repo: Optional[str] = None) -> Dict[str, str]:
    """
    生成GitHub网站或指定GitHub仓库的链接
    
    Args:
        repo: GitHub仓库路径（可选）
        
    Returns:
        包含URL和操作建议的字典
    """
    try:
        if repo:
            # 打开指定的仓库
            url = f'https://github.com/{repo}'
            message = f'已为您生成GitHub仓库链接，点击即可访问: {repo}'
        else:
            # 打开GitHub首页
            url = 'https://github.com'
            message = '已为您生成GitHub首页链接，点击即可访问'
        
        return {
            'url': url,
            'action': 'open',
            'message': message
        }
    except Exception as e:
        raise Exception(f"生成GitHub链接失败: {str(e)}")


@tool_manager.register_tool(
    name='open_youtube',
    description='生成YouTube网站或视频搜索的链接。适用于用户想要观看视频或访问YouTube的情况。',
    parameters={
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': '搜索关键词（可选），例如：Python教程。如果不提供，则打开YouTube首页。'
            }
        },
        'required': []
    }
)
def open_youtube(query: Optional[str] = None) -> Dict[str, str]:
    """
    生成YouTube网站或视频搜索的链接
    
    Args:
        query: 搜索关键词（可选）
        
    Returns:
        包含URL和操作建议的字典
    """
    try:
        if query:
            # 搜索视频
            url = f'https://www.youtube.com/results?search_query={query}'
            message = f'已为您生成YouTube搜索链接，点击即可搜索: {query}'
        else:
            # 打开YouTube首页
            url = 'https://www.youtube.com'
            message = '已为您生成YouTube首页链接，点击即可访问'
        
        return {
            'url': url,
            'action': 'open',
            'message': message
        }
    except Exception as e:
        raise Exception(f"生成YouTube链接失败: {str(e)}")