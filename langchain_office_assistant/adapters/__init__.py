"""
AI平台适配器统一管理器
支持多平台切换和统一接口
"""
from typing import List, Dict, Optional, Any, Type
from enum import Enum
import logging

from .base import PlatformAdapter, ModelInfo
from .dashscope import DashScopeAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .gemini import GoogleAdapter
from .azure import AzureAdapter
from .zhipu import ZhipuAdapter
from .spark import SparkAdapter
from .ernie import ErnieAdapter
from .doubao import DoubaoAdapter
from .custom import CustomAdapter

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """支持的AI平台类型"""
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE = "azure"
    ZHIPU = "zhipu"
    SPARK = "spark"
    ERNIE = "ernie"
    DOUBAO = "doubao"
    CUSTOM = "custom"


class AdapterManager:
    """多平台适配器管理器"""

    _adapters: Dict[PlatformType, Type[PlatformAdapter]] = {
        PlatformType.DASHSCOPE: DashScopeAdapter,
        PlatformType.OPENAI: OpenAIAdapter,
        PlatformType.ANTHROPIC: AnthropicAdapter,
        PlatformType.GEMINI: GoogleAdapter,
        PlatformType.AZURE: AzureAdapter,
        PlatformType.ZHIPU: ZhipuAdapter,
        PlatformType.SPARK: SparkAdapter,
        PlatformType.ERNIE: ErnieAdapter,
        PlatformType.DOUBAO: DoubaoAdapter,
        PlatformType.CUSTOM: CustomAdapter,
    }

    _platform_configs: Dict[PlatformType, Dict[str, Any]] = {
        PlatformType.DASHSCOPE: {
            "name": "阿里百炼 (DashScope)",
            "description": "阿里云百炼平台，支持482+模型",
            "default_api_base": "https://dashscope.aliyuncs.com",
            "website": "https://bailian.console.aliyun.com",
            "features": ["文本生成", "多模态", "函数调用", "长上下文"]
        },
        PlatformType.OPENAI: {
            "name": "OpenAI",
            "description": "OpenAI官方API，支持GPT-4、GPT-3.5等",
            "default_api_base": "https://api.openai.com/v1",
            "website": "https://platform.openai.com",
            "features": ["文本生成", "图像理解", "函数调用", "o1推理"]
        },
        PlatformType.ANTHROPIC: {
            "name": "Anthropic (Claude)",
            "description": "Anthropic Claude系列模型",
            "default_api_base": "https://api.anthropic.com/v1",
            "website": "https://console.anthropic.com",
            "features": ["文本生成", "视觉理解", "长上下文", "安全对齐"]
        },
        PlatformType.GEMINI: {
            "name": "Google Gemini",
            "description": "Google Gemini系列模型",
            "default_api_base": "https://generativelanguage.googleapis.com/v1beta",
            "website": "https://aistudio.google.com",
            "features": ["多模态", "超长上下文", "实时推理", "免费额度"]
        },
        PlatformType.AZURE: {
            "name": "Azure OpenAI",
            "description": "Azure云部署的OpenAI模型",
            "default_api_base": "",
            "website": "https://azure.microsoft.com/services/cognitive-services/openai",
            "features": ["企业级安全", "合规性", "私有部署", "SLA保障"]
        },
        PlatformType.ZHIPU: {
            "name": "智谱AI (Zhipu AI)",
            "description": "智谱AI GLM系列模型，GLM-4、GLM-3.5等",
            "default_api_base": "https://open.bigmodel.cn/api/paas/v4",
            "website": "https://bigmodel.cn",
            "features": ["文本生成", "长上下文", "函数调用", "多模态"]
        },
        PlatformType.SPARK: {
            "name": "讯飞星火 (iFlyTek Spark)",
            "description": "科大讯飞星火大模型，Spark-4.0、3.5等",
            "default_api_base": "https://spark-api.xf-yun.com/v3.5/chat",
            "website": "https://www.xfyun.cn",
            "features": ["文本生成", "长上下文", "函数调用", "多模态"]
        },
        PlatformType.ERNIE: {
            "name": "文心一言 (ERNIE)",
            "description": "百度文心一言，ERNIE-4.0、3.5等",
            "default_api_base": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
            "website": "https://cloud.baidu.com/product/wenxinworkshop",
            "features": ["文本生成", "长上下文", "函数调用", "企业级"]
        },
        PlatformType.DOUBAO: {
            "name": "豆包 (Doubao)",
            "description": "字节跳动豆包大模型，火山引擎ARK",
            "default_api_base": "https://ark.cn-beijing.volces.com/api/v3",
            "website": "https://www.volcengine.com/product/ark",
            "features": ["文本生成", "长上下文", "函数调用", "高性价比"]
        },
        PlatformType.CUSTOM: {
            "name": "自定义API (Custom)",
            "description": "支持任意OpenAI兼容的第三方API",
            "default_api_base": "http://localhost:8080/v1",
            "website": "",
            "features": ["灵活配置", "API兼容", "本地部署", "第三方平台"]
        },
    }

    def __init__(self):
        self._active_adapters: Dict[PlatformType, PlatformAdapter] = {}
        self._current_platform: Optional[PlatformType] = None

    def register_adapter(self, platform: PlatformType, adapter_class: Type[PlatformAdapter]):
        """注册新的适配器"""
        self._adapters[platform] = adapter_class
        logger.info(f"Registered adapter for {platform.value}")

    def create_adapter(
        self,
        platform: PlatformType,
        api_key: str,
        **kwargs
    ) -> PlatformAdapter:
        """创建平台适配器"""
        if platform not in self._adapters:
            raise ValueError(f"Unsupported platform: {platform.value}")

        adapter_class = self._adapters[platform]

        if platform == PlatformType.DASHSCOPE:
            kwargs.setdefault("api_base", "https://dashscope.aliyuncs.com")
        elif platform == PlatformType.OPENAI:
            kwargs.setdefault("api_base", "https://api.openai.com/v1")
        elif platform == PlatformType.ANTHROPIC:
            kwargs.setdefault("api_base", "https://api.anthropic.com/v1")
        elif platform == PlatformType.GEMINI:
            kwargs.setdefault("api_base", "https://generativelanguage.googleapis.com/v1beta")
        elif platform == PlatformType.ZHIPU:
            kwargs.setdefault("api_base", "https://open.bigmodel.cn/api/paas/v4")
        elif platform == PlatformType.SPARK:
            kwargs.setdefault("api_base", "https://spark-api.xf-yun.com/v3.5/chat")
        elif platform == PlatformType.ERNIE:
            kwargs.setdefault("api_base", "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat")
        elif platform == PlatformType.DOUBAO:
            kwargs.setdefault("api_base", "https://ark.cn-beijing.volces.com/api/v3")
        elif platform == PlatformType.CUSTOM:
            kwargs.setdefault("api_base", "http://localhost:8080/v1")

        adapter = adapter_class(api_key, **kwargs)
        self._active_adapters[platform] = adapter
        return adapter

    def get_adapter(self, platform: PlatformType) -> Optional[PlatformAdapter]:
        """获取已创建的适配器"""
        return self._active_adapters.get(platform)

    def set_current_platform(self, platform: PlatformType):
        """设置当前平台"""
        self._current_platform = platform
        logger.info(f"Current platform set to: {platform.value}")

    def get_current_platform(self) -> Optional[PlatformType]:
        """获取当前平台"""
        return self._current_platform

    def get_current_adapter(self) -> Optional[PlatformAdapter]:
        """获取当前适配器"""
        if self._current_platform:
            return self._active_adapters.get(self._current_platform)
        return None

    def list_platforms(self) -> List[Dict[str, Any]]:
        """列出所有支持的平台"""
        return [
            {
                "id": p.value,
                "name": config["name"],
                "description": config["description"],
                "website": config["website"],
                "features": config["features"],
                "is_active": p in self._active_adapters,
                "is_current": p == self._current_platform
            }
            for p, config in self._platform_configs.items()
        ]

    def get_platform_info(self, platform: PlatformType) -> Optional[Dict[str, Any]]:
        """获取平台信息"""
        config = self._platform_configs.get(platform)
        if not config:
            return None
        return {
            "id": platform.value,
            **config,
            "is_active": platform in self._active_adapters,
            "is_current": platform == self._current_platform
        }


_manager = None

def get_adapter_manager() -> AdapterManager:
    """获取全局适配器管理器实例"""
    global _manager
    if _manager is None:
        _manager = AdapterManager()
    return _manager


def create_adapter(
    platform: str,
    api_key: str,
    **kwargs
) -> Optional[PlatformAdapter]:
    """快捷函数：创建指定平台的适配器"""
    try:
        platform_type = PlatformType(platform.lower())
    except ValueError:
        logger.error(f"Unknown platform: {platform}")
        return None

    manager = get_adapter_manager()
    return manager.create_adapter(platform_type, api_key, **kwargs)
