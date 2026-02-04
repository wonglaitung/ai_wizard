import os
import requests
import json
import logging

# 配置日志
logger = logging.getLogger(__name__)

# Configuration - only for fallback when no base_url is provided in function calls
api_key = os.getenv('QWEN_API_KEY', '')  # 从环境变量读取API密钥
default_base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'  # 硬编码默认值作为最后的备选
embedding_url = f"{default_base_url}/embeddings"
chat_url = f"{default_base_url}/chat/completions"
max_tokens = int(os.getenv('MAX_TOKENS', 16384))


def _filter_reasoning_content(content):
    """
    过滤掉推理过程，只保留最终回复
    
    新模型（如qwen3）的响应中，content字段可能包含推理过程和最终回复。
    推理过程在前面，与最终回复之间用 "</think>" 分隔。
    此函数提取 "</think>" 之后的最终回复部分。
    
    Args:
        content (str): 包含推理过程和最终回复的完整内容
        
    Returns:
        str: 只包含最终回复的内容
    """
    if not content:
        return content
    
    # 查找第一个 "\n\n" 分隔符
    separator = '</think>'
    if separator in content:
        # 分割内容，只保留 "</think>" 之后的部分
        parts = content.split(separator, 1)
        final_content = parts[1].strip()
        if final_content:
            logger.info(f"[FILTER] 检测到推理过程，已过滤掉 {len(parts[0])} 个字符")
            return final_content
    
    # 如果没有 "</think>" 分隔符，返回原始内容
    return content


def _validate_and_limit_params(temperature, max_tokens, top_p, frequency_penalty):
    """验证并限制参数值在API允许范围内"""
    validated_temperature = max(0.0, min(2.0, temperature))  # 通常temperature范围是0-2
    validated_max_tokens = max(1, min(8192, max_tokens))    # max_tokens通常最大为8192
    validated_top_p = max(0.0, min(1.0, top_p))            # top_p范围是0-1
    validated_frequency_penalty = max(-2.0, min(2.0, frequency_penalty))  # frequency_penalty范围是-2到2
    
    return validated_temperature, validated_max_tokens, validated_top_p, validated_frequency_penalty


def _prepare_messages(query, history):
    """准备消息列表，包含历史记录和当前查询"""
    messages = []
    
    # 添加历史记录到消息列表
    if history:
        for msg in history:
            # 将历史记录中的 'user' 和 'ai' 角色转换为 'user' 和 'assistant'
            role = 'user' if msg['role'] == 'user' else 'assistant'
            messages.append({
                'role': role,
                'content': msg['content']
            })
    
    # 添加当前查询
    messages.append({
        'role': 'user',
        'content': query
    })
    
    return messages


def _validate_api_key(api_key):
    """检查API密钥是否设置"""
    if api_key is None:
        api_key = os.getenv('QWEN_API_KEY', '')
    
    if not api_key:
        raise ValueError("未提供API密钥")
    
    return api_key


def _get_base_url(base_url):
    """获取基础URL"""
    if base_url is None:
        base_url = default_base_url
    return base_url


def _create_headers(api_key):
    """创建请求头"""
    return {
        'Authorization': f'Bearer {api_key}'
    }


def _ensure_utf8_encoding(query):
    """确保查询文本是 UTF-8 编码"""
    if isinstance(query, str):
        query = query.encode('utf-8').decode('utf-8')
    return query


def _handle_error(error):
    """统一的错误处理"""
    logger.error(f'Error during requests POST: {error}')
    # 检查是否是'choices'键缺失的错误
    if "'choices'" in str(error):
        logger.error("API响应格式错误：响应中缺少'choices'字段。这可能表示：")
        logger.error("1. API密钥无效")
        logger.error("2. 模型名称不正确")
        logger.error("3. API端点URL不正确")
        logger.error("4. 其他API错误")
    raise error  # Re-raise the error for the caller to handle


def _handle_http_error(http_err):
    """统一的HTTP错误处理"""
    logger.error(f'HTTP error during requests POST: {http_err}')
    logger.error(f'Response content: {http_err.response.text if http_err.response else "No response"}')
    raise Exception(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text if http_err.response else str(http_err)}")


def embed_with_llm(query, base_url=None, api_key=None):
    """
    Generate embeddings for a given query using Qwen's embedding API.
    
    Args:
        query (str): The text to generate embeddings for
        base_url (str): The base URL for the API. If None, uses default.
        api_key (str): API key for authentication. If None, uses environment variable.
        
    Returns:
        dict: The embedding vector data
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        api_key = _validate_api_key(api_key)
        
        # 使用传入的base_url或默认URL
        base_url = _get_base_url(base_url)
        
        headers = _create_headers(api_key)
        
        # 确保查询文本是 UTF-8 编码
        query = _ensure_utf8_encoding(query)
        
        payload = {
            'model': 'text-embedding-v4',
            'input': query
        }
        
        # 构建完整的API URL
        api_url = f"{base_url}/embeddings"
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()['data'][0]  # Return the embedding vector
    except requests.exceptions.HTTPError as http_err:
        _handle_http_error(http_err)
    except Exception as error:
        logger.error(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle


def _prepare_payload(messages, model, stream, temperature, max_tokens, top_p, frequency_penalty, enable_thinking, tools=None):
    """准备请求载荷"""
    validated_temperature, validated_max_tokens, validated_top_p, validated_frequency_penalty = _validate_and_limit_params(
        temperature, max_tokens, top_p, frequency_penalty
    )
    
    payload = {
        'model': model,
        'messages': messages,
        'stream': stream,
        'top_p': validated_top_p,
        'temperature': validated_temperature,
        'max_tokens': validated_max_tokens,
        'frequency_penalty': validated_frequency_penalty,
        'seed': 1368,
        'enable_thinking': enable_thinking
    }
    
    # 如果提供了tools参数，添加到payload中
    if tools:
        payload['tools'] = tools
    
    return payload


def create_model_params(settings=None, api_key=None, default_model='qwen-max', default_temperature=0.7, 
                       default_max_tokens=8196, default_top_p=0.9, default_frequency_penalty=0.5):
    """
    创建模型参数字典，避免在多个模块中重复相同的参数配置逻辑
    
    Args:
        settings (dict): 包含模型设置的字典
        api_key (str): API密钥
        default_model (str): 默认模型名称
        default_temperature (float): 默认温度参数
        default_max_tokens (int): 默认最大token数
        default_top_p (float): 默认top_p参数
        default_frequency_penalty (float): 默认频率惩罚参数
        
    Returns:
        dict: 包含模型参数的字典
    """
    if settings is None:
        settings = {}
    
    return {
        'model': settings.get('modelName', default_model),
        'temperature': settings.get('temperature', default_temperature),
        'max_tokens': settings.get('maxTokens', default_max_tokens), 
        'top_p': settings.get('topP', default_top_p),
        'frequency_penalty': settings.get('frequencyPenalty', default_frequency_penalty),
        'api_key': api_key,
        'base_url': settings.get('baseUrl', None),
    }


def _process_streaming_response(response, model):
    """处理流式响应，过滤掉推理过程"""
    full_response = ""
    in_reasoning = True  # 初始状态：假设在推理过程中
    buffer = ""  # 缓冲区，用于检测 "</think>" 分隔符
    separator = '</think>'

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                data = decoded_line[6:]  # Remove 'data: ' prefix
                if data != '[DONE]':
                    try:
                        json_data = json.loads(data)
                        if 'choices' in json_data and len(json_data['choices']) > 0:
                            delta = json_data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content = delta['content']
                                full_response += content
                                
                                # 如果在推理过程中，将内容添加到缓冲区
                                if in_reasoning:
                                    buffer += content
                                    # 检查缓冲区中是否包含 "</think>" 分隔符
                                    if separator in buffer:
                                        in_reasoning = False
                                        # 提取 "</think>" 之后的部分并输出
                                        parts = buffer.split(separator, 1)
                                        final_part = parts[1]
                                        if final_part:
                                            yield final_part
                                        logger.info(f"[STREAM FILTER] 检测到推理过程结束，开始输出最终回复")
                                else:
                                    # 已经在最终回复阶段，直接输出
                                    yield content
                    except json.JSONDecodeError:
                        # 如果不是JSON数据，跳过
                        continue
    # 记录响应信息
    logger.info(f"[LLM RESPONSE] Model {model} response: {full_response[:200]}{'...' if len(full_response) > 200 else ''}")
    
    return full_response


def chat_with_llm_stream(query, model='qwen-max', temperature=0.7, max_tokens=8196, top_p=0.9, frequency_penalty=0.5, api_key=None, base_url=None, enable_thinking=False, history=None):
    """
    Generate a streaming response from Qwen model for a given query.
    
    Args:
        query (str): The user's query
        model (str): The model name to use. Default is 'qwen-max'.
        temperature (float): Controls randomness in output. Default is 0.7.
        max_tokens (int): Maximum number of tokens to generate. Default is 8196.
        top_p (float): Controls diversity of output. Default is 0.9.
        frequency_penalty (float): Controls repetition. Default is 0.5.
        api_key (str): API key for authentication. If None, uses environment variable. Default is None.
        base_url (str): The base URL for the API. If None, uses default.
        enable_thinking (bool): Whether to enable thinking mode (推理模式). Default is False.
        history (list): Chat history containing previous messages. Default is None.
        
    Yields:
        str: Chunks of the model's response text
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        api_key = _validate_api_key(api_key)
        
        # 使用传入的base_url或默认URL
        base_url = _get_base_url(base_url)
        
        headers = _create_headers(api_key)
        
        # 确保查询文本是 UTF-8 编码
        query = _ensure_utf8_encoding(query)
        
        # 准备消息列表，包含历史记录和当前查询
        messages = _prepare_messages(query, history)
        
        payload = _prepare_payload(messages, model, True, temperature, max_tokens, top_p, frequency_penalty, enable_thinking)
        
        # 记录调用信息
        logger.info(f"[LLM CALL] Calling model: {model} with query: {query}")
        
        # 构建完整的API URL
        api_url = f"{base_url}/chat/completions"
        response = requests.post(api_url, headers=headers, json=payload, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # 处理流式响应
        return _process_streaming_response(response, model)
        
    except requests.exceptions.HTTPError as http_err:
        _handle_http_error(http_err)
    except Exception as error:
        _handle_error(error)


def chat_with_llm(query, model='qwen-max', temperature=0.7, max_tokens=8196, top_p=0.9, frequency_penalty=0.5, api_key=None, base_url=None, enable_thinking=False, history=None, tools=None):
    """
    Generate a response from Qwen model for a given query.
    
    Args:
        query (str): The user's query
        model (str): The model name to use. Default is 'qwen-max'.
        temperature (float): Controls randomness in output. Default is 0.7.
        max_tokens (int): Maximum number of tokens to generate. Default is 8196.
        top_p (float): Controls diversity of output. Default is 0.9.
        frequency_penalty (float): Controls repetition. Default is 0.5.
        api_key (str): API key for authentication. If None, uses environment variable. Default is None.
        base_url (str): The base URL for the API. If None, uses default.
        enable_thinking (bool): Whether to enable thinking mode (推理模式). Default is False.
        history (list): Chat history containing previous messages. Default is None.
        tools (list): List of tools available for function calling. Default is None.
        
    Returns:
        dict: 包含响应内容和tool_calls信息的字典
            {
                'content': str,  # 文本响应内容
                'tool_calls': list or None  # 工具调用信息
            }
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        api_key = _validate_api_key(api_key)
        
        # 使用传入的base_url或默认URL
        base_url = _get_base_url(base_url)
        
        headers = _create_headers(api_key)
        
        # 确保查询文本是 UTF-8 编码
        query = _ensure_utf8_encoding(query)
        
        # 准备消息列表，包含历史记录和当前查询
        messages = _prepare_messages(query, history)
        
        payload = _prepare_payload(messages, model, False, temperature, max_tokens, top_p, frequency_penalty, enable_thinking, tools)
        
        # 记录调用信息
        logger.info(f"[LLM CALL] Calling model: {model} with query: {query}")
        if tools:
            logger.info(f"[LLM CALL] Tools provided: {len(tools)} tools")
        
        # 构建完整的API URL
        api_url = f"{base_url}/chat/completions"
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        response_json = response.json()
        
        # 检查响应是否包含预期的结构
        if 'choices' not in response_json or not response_json['choices']:
            logger.error(f'API响应缺少choices字段: {response_json}')
            raise Exception(f'API响应格式错误: {response_json}')
        
        choice = response_json['choices'][0]
        if 'message' not in choice:
            logger.error(f'API响应缺少message内容: {response_json}')
            raise Exception(f'API响应格式错误: {response_json}')
        
        message = choice['message']
        
        # 提取内容和工具调用信息
        content = message.get('content', '')
        tool_calls = message.get('tool_calls', None)
        
        # 过滤掉推理过程，只保留最终回复
        if content:
            content = _filter_reasoning_content(content)
        
        # 记录响应信息
        if content:
            logger.info(f"[LLM RESPONSE] Model {model} response: {content[:200]}{'...' if len(content) > 200 else ''}")
        if tool_calls:
            logger.info(f"[LLM RESPONSE] Tool calls requested: {len(tool_calls)} calls")
        
        return {
            'content': content,
            'tool_calls': tool_calls
        }
    except requests.exceptions.HTTPError as http_err:
        _handle_http_error(http_err)
    except Exception as error:
        _handle_error(error)
