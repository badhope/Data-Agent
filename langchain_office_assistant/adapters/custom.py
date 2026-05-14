"""
第三方兼容API平台适配器
支持任意OpenAI兼容的API接口
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class CustomAdapter(PlatformAdapter):
    """自定义/第三方兼容API平台适配器"""

    def get_platform_name(self) -> str:
        return self.config.get("platform_name", "自定义API (Custom)")

    def get_api_base(self) -> str:
        return self.config.get("api_base", "http://localhost:8080/v1")

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        custom_models = self.config.get("models", [])
        known_models = []

        if custom_models:
            for m in custom_models:
                if isinstance(m, dict):
                    model_info = ModelInfo(
                        name=m.get("name", ""),
                        display_name=m.get("display_name", m.get("name", "")),
                        description=m.get("description", ""),
                        provider=m.get("provider", "custom"),
                        capabilities=m.get("capabilities", ["文本生成"]),
                        status="available"
                    )
                else:
                    model_info = ModelInfo(
                        name=str(m),
                        display_name=str(m),
                        description="自定义模型",
                        provider="custom",
                        capabilities=["文本生成"],
                        status="available"
                    )
                known_models.append(model_info)

        if not known_models:
            known_models = [
                ModelInfo(
                    name="model",
                    display_name="自定义模型",
                    description="默认自定义模型",
                    provider="custom",
                    capabilities=["文本生成"],
                    status="available"
                ),
            ]

        self.model_cache = known_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(known_models)} models from custom API")
        return known_models

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            extra_headers = self.config.get("extra_headers", {})
            headers.update(extra_headers)

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
                error_msg = "请求失败"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = response.text
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
        model = model or self.current_model or self.config.get("default_model", "model")
        url = f"{self.get_api_base()}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        extra_headers = self.config.get("extra_headers", {})
        headers.update(extra_headers)

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
                error_msg = "请求失败"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = response.text
                return {
                    "success": False,
                    "error": error_msg,
                    "raw_response": response.text
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表"""
        models = []
        for m in self.list_models():
            models.append(m.name)
        return models[:5] if models else ["model"]
