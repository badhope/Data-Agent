"""
多平台模型管理器
统一管理所有AI平台的模型选择和切换
"""
from typing import List, Dict, Optional, Any
import time
import requests
import logging
from langchain_office_assistant.adapters import (
    PlatformAdapter,
    PlatformType,
    AdapterManager,
    get_adapter_manager,
    create_adapter,
    ModelInfo
)
from langchain_office_assistant.utils.config import config

logger = logging.getLogger(__name__)


class MultiPlatformModelManager:
    """多平台模型管理器"""

    def __init__(self):
        self.manager = get_adapter_manager()
        self._current_platform: Optional[PlatformType] = None
        self._current_adapter: Optional[PlatformAdapter] = None
        self._initialized = False

    def initialize(self):
        """初始化：从配置自动加载已配置的平台"""
        if self._initialized:
            return

        try:
            if config.openai_api_base and "dashscope" in config.openai_api_base:
                if config.openai_api_key:
                    self.setup_platform(
                        PlatformType.DASHSCOPE.value,
                        config.openai_api_key
                    )

            self._initialized = True
            logger.info("MultiPlatformModelManager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize: {e}")

    def setup_platform(self, platform: str, api_key: str, **kwargs) -> bool:
        """设置平台配置"""
        try:
            platform_type = PlatformType(platform.lower())
        except ValueError:
            logger.error(f"Unknown platform: {platform}")
            return False

        try:
            adapter = self.manager.create_adapter(platform_type, api_key, **kwargs)
            self._current_platform = platform_type
            self._current_adapter = adapter
            self.manager.set_current_platform(platform_type)
            logger.info(f"Platform setup: {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup platform {platform}: {e}")
            return False

    def switch_platform(self, platform: str) -> bool:
        """切换平台"""
        try:
            platform_type = PlatformType(platform.lower())
            adapter = self.manager.get_adapter(platform_type)

            if not adapter:
                logger.warning(f"Platform {platform} not configured. Use setup_platform first.")
                return False

            self._current_platform = platform_type
            self._current_adapter = adapter
            self.manager.set_current_platform(platform_type)
            logger.info(f"Switched to platform: {platform}")
            return True

        except ValueError:
            logger.error(f"Unknown platform: {platform}")
            return False

    def get_current_platform(self) -> Optional[str]:
        """获取当前平台"""
        return self._current_platform.value if self._current_platform else None

    def get_current_adapter(self) -> Optional[PlatformAdapter]:
        """获取当前适配器"""
        return self._current_adapter

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取当前平台的模型列表"""
        if not self._current_adapter:
            logger.warning("No platform configured")
            return []

        return self._current_adapter.list_models(force_refresh)

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        if not self._current_adapter:
            return {"success": False, "error": "No platform configured"}

        return self._current_adapter.test_model(model_name)

    def set_model(self, model_name: str) -> bool:
        """设置当前模型"""
        if not self._current_adapter:
            return False

        return self._current_adapter.set_model(model_name)

    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        if not self._current_adapter:
            return None

        return self._current_adapter.get_current_model()

    def search_models(self, keyword: str) -> List[ModelInfo]:
        """搜索模型"""
        if not self._current_adapter:
            return []

        return self._current_adapter.search_models(keyword)

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型"""
        if not self._current_adapter:
            return []

        return self._current_adapter.get_recommended_models()

    def test_all_recommended(self) -> Dict[str, Any]:
        """测试所有推荐模型"""
        if not self._current_adapter:
            return {"available": [], "unavailable": [], "details": {}}

        return self._current_adapter.test_all_recommended()

    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> Dict[str, Any]:
        """发送对话请求"""
        if not self._current_adapter:
            return {"success": False, "error": "No platform configured"}

        return self._current_adapter.chat(messages, model, **kwargs)

    def list_platforms(self) -> List[Dict[str, Any]]:
        """列出所有支持的平台"""
        platforms = self.manager.list_platforms()

        result = []
        for p in platforms:
            platform_type = PlatformType(p["id"])
            adapter = self.manager.get_adapter(platform_type)
            p["is_configured"] = adapter is not None
            p["is_active"] = self._current_platform == platform_type
            result.append(p)

        return result

    def get_platform_models(self, platform: str) -> List[ModelInfo]:
        """获取指定平台的模型列表"""
        try:
            platform_type = PlatformType(platform.lower())
            adapter = self.manager.get_adapter(platform_type)

            if not adapter:
                adapter = self.manager.create_adapter(platform_type, "")
                if platform_type == PlatformType.DASHSCOPE:
                    adapter = self.manager.create_adapter(
                        platform_type,
                        config.openai_api_key or "",
                        api_base="https://dashscope.aliyuncs.com"
                    )

            return adapter.list_models()

        except Exception as e:
            logger.error(f"Failed to get models for {platform}: {e}")
            return []

    def chat_with_platform(
        self,
        platform: str,
        messages: List[Dict],
        model: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """使用指定平台发送对话请求"""
        try:
            platform_type = PlatformType(platform.lower())
            adapter = self.manager.get_adapter(platform_type)

            if not adapter:
                return {"success": False, "error": f"Platform {platform} not configured"}

            return adapter.chat(messages, model, **kwargs)

        except ValueError:
            return {"success": False, "error": f"Unknown platform: {platform}"}


_manager = None

def get_model_manager() -> MultiPlatformModelManager:
    """获取全局模型管理器实例"""
    global _manager
    if _manager is None:
        _manager = MultiPlatformModelManager()
        _manager.initialize()
    return _manager


def setup_platform(platform: str, api_key: str, **kwargs) -> bool:
    """快捷函数：设置平台"""
    return get_model_manager().setup_platform(platform, api_key, **kwargs)


def switch_platform(platform: str) -> bool:
    """快捷函数：切换平台"""
    return get_model_manager().switch_platform(platform)


def list_platforms() -> List[Dict[str, Any]]:
    """快捷函数：列出平台"""
    return get_model_manager().list_platforms()


def list_models(force_refresh: bool = False) -> List[ModelInfo]:
    """快捷函数：列出模型"""
    return get_model_manager().list_models(force_refresh)


def test_model(model_name: str) -> Dict[str, Any]:
    """快捷函数：测试模型"""
    return get_model_manager().test_model(model_name)


def search_models(keyword: str) -> List[ModelInfo]:
    """快捷函数：搜索模型"""
    return get_model_manager().search_models(keyword)


def chat(messages: List[Dict], model: str = None, **kwargs) -> Dict[str, Any]:
    """快捷函数：发送对话"""
    return get_model_manager().chat(messages, model, **kwargs)
