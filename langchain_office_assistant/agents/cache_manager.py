"""
智能缓存管理器
多层次缓存，提高性能
"""
from typing import Dict, Any, Optional, Callable, Any
import time
import hashlib
import json
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import threading


class CacheType(Enum):
    """缓存类型"""
    MEMORY = "memory"
    LRU = "lru"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    ttl: float
    hits: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:
            return False
        return time.time() - self.timestamp > self.ttl


class MemoryCache:
    """内存缓存"""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            entry.hits += 1
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: float = None):
        """设置缓存"""
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_lru()

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl or self._default_ttl
            )

    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def _evict_lru(self):
        """淘汰最少使用的条目"""
        if not self._cache:
            return

        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, self._cache[k].timestamp)
        )
        del self._cache[lru_key]
        self._stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": f"{hit_rate:.2%}"
            }


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self._caches: Dict[str, MemoryCache] = {
            "default": MemoryCache(max_size=1000, default_ttl=3600),
            "llm": MemoryCache(max_size=100, default_ttl=7200),
            "vector": MemoryCache(max_size=500, default_ttl=3600),
            "result": MemoryCache(max_size=200, default_ttl=1800),
        }

    def get_cache(self, name: str = "default") -> MemoryCache:
        """获取指定缓存"""
        return self._caches.get(name, self._caches["default"])

    def cache_result(self, cache_name: str = "default", ttl: float = None):
        """缓存结果装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache = self.get_cache(cache_name)
                cache_key = self._generate_key(func.__name__, args, kwargs)

                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    return cached_value

                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator

    def invalidate(self, cache_name: str = "default", pattern: str = None):
        """失效缓存"""
        cache = self.get_cache(cache_name)
        if pattern:
            with cache._lock:
                keys_to_delete = [k for k in cache._cache.keys() if pattern in k]
                for key in keys_to_delete:
                    cache.delete(key)
        else:
            cache.clear()

    @staticmethod
    def _generate_key(func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = {
            "func": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存统计"""
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }


_cache_manager = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
