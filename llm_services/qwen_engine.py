import os
import requests
import json

# Configuration
api_key = os.getenv('QWEN_API_KEY', '')  # 从环境变量读取API密钥
embedding_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
chat_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
max_tokens = int(os.getenv('MAX_TOKENS', 16384))

def embed_with_llm(query):
    """
    Generate embeddings for a given query using Qwen's embedding API.
    
    Args:
        query (str): The text to generate embeddings for
        
    Returns:
        dict: The embedding vector data
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        if not api_key:
            raise ValueError("QWEN_API_KEY 环境变量未设置")
        
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
        
        response = requests.post(embedding_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()['data'][0]  # Return the embedding vector
    except Exception as error:
        print(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle

def chat_with_llm_stream(query, enable_thinking=True):
    """
    Generate a streaming response from Qwen model for a given query.
    
    Args:
        query (str): The user's query
        enable_thinking (bool): Whether to enable thinking mode (推理模式). Default is True.
        
    Yields:
        str: Chunks of the model's response text
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        if not api_key:
            raise ValueError("QWEN_API_KEY 环境变量未设置")
        
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        # 确保查询文本是 UTF-8 编码
        if isinstance(query, str):
            query = query.encode('utf-8').decode('utf-8')
        
        payload = {
            'model': 'qwen-plus-2025-07-28',
            'messages': [{'role': 'user', 'content': query}],
            'stream': True,
            'top_p': 0.2,
            'temperature': 0.05,
            'max_tokens': max_tokens,
            'seed': 1368,
            'enable_thinking': enable_thinking  # 使用传入的参数
        }
        
        response = requests.post(chat_url, headers=headers, json=payload, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # 处理流式响应
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
                                    yield delta['content']
                        except json.JSONDecodeError:
                            # 如果不是JSON数据，跳过
                            continue
    except Exception as error:
        print(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle

def chat_with_llm(query, enable_thinking=True):
    """
    Generate a response from Qwen model for a given query.
    
    Args:
        query (str): The user's query
        enable_thinking (bool): Whether to enable thinking mode (推理模式). Default is True.
        
    Returns:
        str: The model's response text
        
    Raises:
        Exception: If the API request fails
    """
    try:
        # 检查 API 密钥是否设置
        if not api_key:
            raise ValueError("QWEN_API_KEY 环境变量未设置")
        
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        # 确保查询文本是 UTF-8 编码
        if isinstance(query, str):
            query = query.encode('utf-8').decode('utf-8')
        
        payload = {
            'model': 'qwen-plus-2025-07-28',
            'messages': [{'role': 'user', 'content': query}],
            'stream': False,
            'top_p': 0.2,
            'temperature': 0.05,
            'max_tokens': max_tokens,
            'seed': 1368,
            'enable_thinking': enable_thinking  # 使用传入的参数
        }
        
        response = requests.post(chat_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()['choices'][0]['message']['content']  # Return the response text
    except Exception as error:
        print(f'Error during requests POST: {error}')
        raise error  # Re-raise the error for the caller to handle
