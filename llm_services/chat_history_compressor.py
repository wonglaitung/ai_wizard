"""
聊天历史压缩器模块
用于压缩聊天历史记录，确保不超过最大token限制
包含智能摘要功能，在简单截断无法满足限制时调用大模型进行摘要
"""

from typing import List, Dict, Any, Optional
import logging
import os
from .qwen_engine import chat_with_llm

logger = logging.getLogger(__name__)

def estimate_token_count(text: str) -> int:
    """
    估算文本的token数量
    
    Args:
        text (str): 要估算的文本
        
    Returns:
        int: 估算的token数量
    """
    if not text:
        return 0
    
    # 简单的token估算方法，可根据需要调整
    # 对于中文文本，每个汉字大约为1-2个token
    # 对于英文文本，大约每4个字符为1个token
    token_count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            token_count += 1.5
        else:
            token_count += 0.25
    
    return int(token_count)


def compress_chat_history(chat_history: List[Dict[str, Any]], max_tokens: int = 8196, keep_recent_ratio: float = 0.7, settings: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    压缩聊天历史记录，确保不超过最大token限制
    
    Args:
        chat_history (list): 聊天历史记录列表
        max_tokens (int): 最大token限制
        keep_recent_ratio (float): 保留最近对话的比例，默认0.7（保留70%最近的对话）
        settings (dict): 模型设置参数
        
    Returns:
        list: 压缩后的聊天历史记录
    """
    if not chat_history:
        return []
    
    # 首先估算当前历史记录的总token数
    total_token_count = 0
    for msg in chat_history:
        if isinstance(msg, dict) and 'content' in msg:
            total_token_count += estimate_token_count(msg['content'])
    
    # 如果当前token数没有超过限制，直接返回原历史记录
    if total_token_count <= max_tokens * 0.7:  # 使用70%作为安全边界
        return chat_history
    
    # 如果超过了限制，则先尝试简单截断
    # 计算需要保留的token数量
    tokens_to_keep = int(max_tokens * keep_recent_ratio)
    
    # 从最近的对话开始保留，直到达到token限制
    compressed_history = []
    current_token_count = 0
    
    # 从后往前遍历，保留最近的对话
    for i in range(len(chat_history) - 1, -1, -1):
        msg = chat_history[i]
        if isinstance(msg, dict) and 'content' in msg:
            msg_token_count = estimate_token_count(msg['content'])
            
            # 如果添加这条消息会超过限制，则停止添加
            if current_token_count + msg_token_count > tokens_to_keep:
                break
            
            # 在列表开头插入消息（以保持正确的顺序）
            compressed_history.insert(0, msg)
            current_token_count += msg_token_count
    
    # 如果简单截断后仍然超过限制，使用大模型进行摘要
    if current_token_count > max_tokens * 0.6:  # 如果截断后仍占用超过60%的token
        try:
            # 构建提示词，要求大模型总结历史对话
            history_text = ""
            for msg in compressed_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_text += f"{role}: {content}\n"
            
            if history_text.strip():
                api_key = os.getenv('QWEN_API_KEY', '')
                
                # 如果没有API密钥，回退到简单截断
                if not api_key:
                    logger.warning('未设置API密钥，使用简单截断策略')
                    return compressed_history
                
                summary_prompt = f"""
请将以下对话历史总结为一个简短的上下文摘要，保留关键信息和对话要点：

{history_text}

请提供一个简洁的对话摘要，不要超过200个字。
"""
                
                # 准备模型参数 - 使用传入的settings参数
                settings = settings or {}  # 使用传入的settings参数或空字典
                
                model_params = {
                    'model': settings.get('modelName', 'qwen-max'),
                    'temperature': settings.get('temperature', 0.3),  # 摘要生成使用较低的温度以获得更稳定的结果
                    'max_tokens': settings.get('maxTokens', 2048),  # 使用用户配置的值，但确保足够大
                    'top_p': settings.get('topP', 0.9),
                    'frequency_penalty': settings.get('frequencyPenalty', 0.5),
                    'api_key': api_key,
                    'base_url': settings.get('baseUrl', None),  # 使用settings中的baseUrl
                }
                
                # 调用大模型生成摘要
                summary = chat_with_llm(summary_prompt, **model_params)
                
                # 用摘要替换历史记录，只保留最后一条消息作为上下文
                final_history = [{
                    'role': 'system',
                    'content': f"对话历史摘要: {summary}"
                }]
                
                # 如果原始的当前消息还在限制范围内，也保留
                if len(compressed_history) > 0:
                    # 保留最后一条用户消息和AI回复作为上下文
                    final_history.append(compressed_history[-1])
                
                logger.info(f'聊天历史已通过大模型压缩: 从 {len(chat_history)} 条消息压缩到 {len(final_history)} 条，'
                                f'token数从约 {total_token_count} 压缩到约 {estimate_token_count(summary)}')
                
                return final_history
        except Exception as e:
            logger.error(f'使用大模型压缩历史记录时出错: {e}')
            # 出错时回退到简单截断策略
            logger.info('回退到简单截断策略')
    
    logger.info(f'聊天历史已压缩: 从 {len(chat_history)} 条消息压缩到 {len(compressed_history)} 条，'
                    f'token数从约 {total_token_count} 压缩到约 {current_token_count}')
    
    return compressed_history
