import os
import requests
import json
import logging

# 配置日志
logger = logging.getLogger(__name__)

# Configuration
api_key = os.getenv('QWEN_API_KEY', '')  # 从环境变量读取API密钥
default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
embedding_url = f"{default_base_url}/embeddings"
chat_url = f"{default_base_url}/chat/completions"
max_tokens = int(os.getenv('MAX_TOKENS', 16384))

def embed_with_llm(query, base_url=None):
    """
    Generate embeddings for a given query using Qwen's embedding API.
    
    Args:
        query (str): The text to generate embeddings for
        base_url (str): The base URL for the API. If None, uses default.
        
    Returns:
        dict: The embedding vector data
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        if not api_key:
            raise ValueError("QWEN_API_KEY 环境变量未设置")
        
        # 使用传入的base_url或默认URL
        if base_url is None:
            base_url = default_base_url
        
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        # 确保查询文本是 UTF-8 编码
        if isinstance(query, str):
            query = query.encode('utf-8').decode('utf-8')
        
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
        logger.error(f'HTTP error during requests POST: {http_err}')
        logger.error(f'Response content: {http_err.response.text if http_err.response else "No response"}')
        raise Exception(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text if http_err.response else str(http_err)}")
    except Exception as error:
        logger.error(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle

def chat_with_llm_stream(query, model='qwen-max', temperature=0.7, max_tokens=8196, top_p=0.9, frequency_penalty=0.5, api_key=None, base_url=None, enable_thinking=True, history=None):
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
        enable_thinking (bool): Whether to enable thinking mode (推理模式). Default is True.
        history (list): Chat history containing previous messages. Default is None.
        
    Yields:
        str: Chunks of the model's response text
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        if api_key is None:
            api_key = os.getenv('QWEN_API_KEY', '')
        
        if not api_key:
            raise ValueError("未提供API密钥")
        
        # 使用传入的base_url或默认URL
        if base_url is None:
            base_url = default_base_url
            
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        # 确保查询文本是 UTF-8 编码
        if isinstance(query, str):
            query = query.encode('utf-8').decode('utf-8')
        
        # 准备消息列表，包含历史记录和当前查询
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
        
        # 参数验证和限制
        # 检查并限制参数值在API允许范围内
        validated_temperature = max(0.0, min(2.0, temperature))  # 通常temperature范围是0-2
        validated_max_tokens = max(1, min(8192, max_tokens))    # max_tokens通常最大为8192
        validated_top_p = max(0.0, min(1.0, top_p))            # top_p范围是0-1
        validated_frequency_penalty = max(-2.0, min(2.0, frequency_penalty))  # frequency_penalty范围是-2到2
        
        payload = {
            'model': model,
            'messages': messages,
            'stream': True,
            'top_p': validated_top_p,
            'temperature': validated_temperature,
            'max_tokens': validated_max_tokens,
            'frequency_penalty': validated_frequency_penalty,
            'seed': 1368,
            'enable_thinking': enable_thinking  # 使用传入的参数
        }
        
        # 记录调用信息
        logger.info(f"[LLM CALL] Calling model: {model} with query: {query}")
        
        # 构建完整的API URL
        api_url = f"{base_url}/chat/completions"
        response = requests.post(api_url, headers=headers, json=payload, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # 记录调用信息
        logger.info(f"[LLM CALL] Calling model: {model} with query: {query}")
        
        # 处理流式响应
        full_response = ""
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
                                    yield content
                        except json.JSONDecodeError:
                            # 如果不是JSON数据，跳过
                            continue
        # 记录响应信息
        logger.info(f"[LLM RESPONSE] Model {model} response: {full_response[:200]}{'...' if len(full_response) > 200 else ''}")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f'HTTP error during requests POST: {http_err}')
        logger.error(f'Response content: {http_err.response.text if http_err.response else "No response"}')
        raise Exception(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text if http_err.response else str(http_err)}")
    except Exception as error:
        logger.error(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle

def chat_with_llm(query, model='qwen-max', temperature=0.7, max_tokens=8196, top_p=0.9, frequency_penalty=0.5, api_key=None, base_url=None, enable_thinking=True, history=None):
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
        enable_thinking (bool): Whether to enable thinking mode (推理模式). Default is True.
        history (list): Chat history containing previous messages. Default is None.
        
    Returns:
        str: The model's response text
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        if api_key is None:
            api_key = os.getenv('QWEN_API_KEY', '')
        
        if not api_key:
            raise ValueError("未提供API密钥")
        
        # 使用传入的base_url或默认URL
        if base_url is None:
            base_url = default_base_url
            
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        # 确保查询文本是 UTF-8 编码
        if isinstance(query, str):
            query = query.encode('utf-8').decode('utf-8')
        
        # 准备消息列表，包含历史记录和当前查询
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
        
        # 参数验证和限制
        # 检查并限制参数值在API允许范围内
        validated_temperature = max(0.0, min(2.0, temperature))  # 通常temperature范围是0-2
        validated_max_tokens = max(1, min(8192, max_tokens))    # max_tokens通常最大为8192
        validated_top_p = max(0.0, min(1.0, top_p))            # top_p范围是0-1
        validated_frequency_penalty = max(-2.0, min(2.0, frequency_penalty))  # frequency_penalty范围是-2到2
        
        payload = {
            'model': model,
            'messages': messages,
            'stream': False,
            'top_p': validated_top_p,
            'temperature': validated_temperature,
            'max_tokens': validated_max_tokens,
            'frequency_penalty': validated_frequency_penalty,
            'seed': 1368,
            'enable_thinking': enable_thinking  # 使用传入的参数
        }
        
        # 记录调用信息
        logger.info(f"[LLM CALL] Calling model: {model} with query: {query}")
        
        # 构建完整的API URL
        api_url = f"{base_url}/chat/completions"
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()['choices'][0]['message']['content']  # Return the response text
        
        # 记录响应信息
        logger.info(f"[LLM RESPONSE] Model {model} response: {result[:200]}{'...' if len(result) > 200 else ''}")
        
        return result
    except requests.exceptions.HTTPError as http_err:
        logger.error(f'HTTP error during requests POST: {http_err}')
        logger.error(f'Response content: {http_err.response.text if http_err.response else "No response"}')
        raise Exception(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text if http_err.response else str(http_err)}")
    except Exception as error:
        logger.error(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle
