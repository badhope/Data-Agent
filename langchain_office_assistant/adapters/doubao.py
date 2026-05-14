"""
豆包 (Doubao)平台适配器
支持 Doubao-pro、Doubao-lite 等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class DoubaoAdapter(PlatformAdapter):
    """豆包 (Doubao)平台适配器"""

    def get_platform_name(self) -> str:
        return "豆包 (Doubao)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://ark.cn-beijing.volces.com/api/v3")

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取豆包模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        known_models = [
            ModelInfo(
                name="ep-20240604161735-9zq6v",
                display_name="Doubao-pro-4k",
                description="豆包专业版，4K上下文",
                provider="volcengine",
                capabilities=["文本生成", "函数调用"],
                status="available",
                context_window=4096,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="ep-20240604161735-4w59s",
                display_name="Doubao-pro-32k",
                description="豆包专业版，32K长上下文",
                provider="volcengine",
                capabilities=["文本生成", "长上下文", "函数调用"],
                status="available",
                context_window=32768,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="ep-20240604161735-2x99h",
                display_name="Doubao-lite-4k",
                description="豆包轻量版，4K上下文",
                provider="volcengine",
                capabilities=["文本生成"],
                status="available",
                context_window=4096,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="ep-20240604161735-7t3q8",
                display_name="Doubao-lite-32k",
                description="豆包轻量版，32K长上下文",
                provider="volcengine",
                capabilities=["文本生成", "长上下文"],
                status="available",
                context_window=32768,
                max_output_tokens=4096
            ),
        ]

        self.model_cache = known_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(known_models)} models from Doubao")
        return known_models

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": "say 'OK'"}],
                "max_tokens": 10
            }

            start_time = time.time()
            response = requests.post(url, headers=headers, json=data, timeout=30)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                return {
                    "success": True,
                    "model": model_name,
                    "response": content,
                    "duration_ms": int(duration),
                    "platform": self.get_platform_name()
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                return {
                    "success": False,
                    "model": model_name,
                    "error": self._parse_error(error_msg),
                    "error_detail": error_msg,
                    "platform": self.get_platform_name()
                }

        except Exception as e:
            return {
                "success": False,
                "model": model_name,
                "error": "请求异常",
                "error_detail": str(e),
                "platform": self.get_platform_name()
            }

    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> Dict[str, Any]:
        """发送对话请求"""
        model = model or self.current_model or "ep-20240604161735-9zq6v"
        url = f"{self.get_api_base()}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                error_data = response.json()
                return {
                    "success": False,
                    "error": error_data.get("error", {}).get("message", "请求失败"),
                    "raw_response": response.text
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表"""
        return [
            "ep-20240604161735-9zq6v",
            "ep-20240604161735-4w59s",
            "ep-20240604161735-2x99h",
            "ep-20240604161735-7t3q8",
        ]
