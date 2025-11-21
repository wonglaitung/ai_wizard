"""
缓存管理器模块
用于缓存中间结果以避免重复模型调用和计算
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    缓存管理器，用于缓存分析结果以避免重复计算
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存项数
            ttl: 缓存生存时间（秒）
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times = {}  # 记录访问时间用于LRU淘汰
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, user_request: str, file_content: str, task_type: str) -> str:
        """
        根据用户请求、文件内容和任务类型生成缓存键
        
        Args:
            user_request: 用户请求
            file_content: 文件内容
            task_type: 任务类型
            
        Returns:
            str: 缓存键
        """
        # 创建一个复合键，包含所有相关参数
        key_data = {
            'user_request': user_request,
            'file_content_hash': hashlib.md5(file_content.encode('utf-8')).hexdigest() if file_content else '',
            'task_type': task_type
        }
        
        # 序列化并生成哈希
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def get(self, user_request: str, file_content: str, task_type: str) -> Optional[Dict[str, Any]]:
        """
        从缓存中获取结果
        
        Args:
            user_request: 用户请求
            file_content: 文件内容
            task_type: 任务类型
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的结果或None
        """
        key = self._generate_key(user_request, file_content, task_type)
        
        if key in self.cache:
            cached_item = self.cache[key]
            access_time = self.access_times[key]
            
            # 检查是否过期
            if datetime.now() - access_time < timedelta(seconds=self.ttl):
                self.hit_count += 1
                logger.info(f"缓存命中: {key[:8]}..., 命中率: {self.hit_count/(self.hit_count+self.miss_count)*100:.1f}%")
                return cached_item['data']
            else:
                # 缓存过期，删除
                del self.cache[key]
                del self.access_times[key]
        
        self.miss_count += 1
        logger.info(f"缓存未命中: {key[:8]}..., 命中率: {self.hit_count/(self.hit_count+self.miss_count)*100:.1f}%")
        return None
    
    def set(self, user_request: str, file_content: str, task_type: str, data: Dict[str, Any]):
        """
        将结果存入缓存
        
        Args:
            user_request: 用户请求
            file_content: 文件内容
            task_type: 任务类型
            data: 要缓存的数据
        """
        key = self._generate_key(user_request, file_content, task_type)
        
        # 检查缓存大小限制
        if len(self.cache) >= self.max_size:
            # LRU淘汰：删除最久未访问的项
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            logger.info(f"缓存达到最大大小，淘汰最久未访问项: {oldest_key[:8]}...")
        
        self.cache[key] = {
            'data': data
        }
        self.access_times[key] = datetime.now()
        logger.info(f"缓存设置: {key[:8]}..., 缓存大小: {len(self.cache)}")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate
        }

# 全局缓存实例
cache_manager = CacheManager(max_size=1000, ttl=3600)

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return cache_manager