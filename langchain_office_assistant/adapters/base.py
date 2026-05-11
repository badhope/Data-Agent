"""
多平台AI适配器基类
定义统一的接口和通用功能
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable
from pydantic import BaseModel
import time
import requests
import logging

logger = logging.getLogger(__name__)


class ModelInfo(BaseModel):
    """模型信息"""
    name: str
    display_name: str
    description: str
    provider: str = ""
    capabilities: List[str] = []
    status: str = "unknown"
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_cost_per_1k: Optional[float] = None
    output_cost_per_1k: Optional[float] = None


class PlatformAdapter(ABC):
    """AI平台适配器基类"""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self.current_model = None
        self.model_cache = []
        self.cache_time = 0

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称"""
        pass

    @abstractmethod
    def get_api_base(self) -> str:
        """获取API基础URL"""
        pass

    @abstractmethod
    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取模型列表"""
        pass

    @abstractmethod
    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> Dict[str, Any]:
        """发送对话请求"""
        pass

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def set_model(self, model_name: str) -> bool:
        """设置当前模型"""
        result = self.test_model(model_name)
        if result.get("success"):
            self.current_model = model_name
            logger.info(f"[{self.get_platform_name()}] Model set to: {model_name}")
            return True
        return False

    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.current_model

    def search_models(self, keyword: str) -> List[ModelInfo]:
        """搜索模型"""
        models = self.list_models()
        keyword_lower = keyword.lower()
        results = [
            m for m in models
            if keyword_lower in m.name.lower() or
               keyword_lower in m.display_name.lower() or
               keyword_lower in m.description.lower()
        ]
        return results[:50]

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表"""
        return []

    def test_all_recommended(self) -> Dict[str, Any]:
        """测试所有推荐模型"""
        results = {}
        for model in self.get_recommended_models():
            result = self.test_model(model)
            results[model] = result
            time.sleep(0.3)

        available = [m for m, r in results.items() if r.get("success")]
        unavailable = [m for m, r in results.items() if not r.get("success")]

        return {
            "available": available,
            "unavailable": unavailable,
            "details": results,
            "total_available": len(available)
        }

    def _parse_error(self, error_msg: str) -> str:
        """解析错误信息"""
        error_msg_lower = error_msg.lower()

        if any(keyword in error_msg_lower for keyword in ["free tier", "quota", "额度", "配额", "limit"]):
            return "配额不足或免费额度用尽"
        elif any(keyword in error_msg_lower for keyword in ["not exist", "404", "not found", "不存在"]):
            return "模型不存在"
        elif "stream" in error_msg_lower:
            return "该模型仅支持流式输出"
        elif any(keyword in error_msg_lower for keyword in ["auth", "unauthorized", "invalid", "权限", "密钥"]):
            return "API密钥无效或权限不足"
        elif any(keyword in error_msg_lower for keyword in ["rate", "rate limit", "频率", "限流"]):
            return "请求频率超限"
        else:
            return "模型调用失败"
