"""
智谱AI (Zhipu AI)平台适配器
支持 GLM-4、GLM-3.5-Turbo 等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class ZhipuAdapter(PlatformAdapter):
    """智谱AI (Zhipu AI)平台适配器"""

    def get_platform_name(self) -> str:
        return "智谱AI (Zhipu AI)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://open.bigmodel.cn/api/paas/v4")

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取智谱AI模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        known_models = [
            ModelInfo(
                name="glm-4",
                display_name="GLM-4",
                description="新一代大模型，能力最强，支持长文本处理",
                provider="zhipu",
                capabilities=["文本生成", "长上下文", "函数调用"],
                status="available",
                context_window=128000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="glm-4-flash",
                display_name="GLM-4 Flash",
                description="快速版本，性价比高",
                provider="zhipu",
                capabilities=["文本生成", "长上下文"],
                status="available",
                context_window=128000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="glm-4-plus",
                display_name="GLM-4 Plus",
                description="GLM-4增强版，能力更强",
                provider="zhipu",
                capabilities=["文本生成", "长上下文", "函数调用"],
                status="available",
                context_window=128000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="glm-3-turbo",
                display_name="GLM-3 Turbo",
                description="GLM-3.5 Turbo，稳定可靠",
                provider="zhipu",
                capabilities=["文本生成", "函数调用"],
                status="available",
                context_window=128000,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="glm-4v",
                display_name="GLM-4V",
                description="支持图像理解的多模态模型",
                provider="zhipu",
                capabilities=["文本生成", "视觉理解"],
                status="available",
                context_window=2048,
                max_output_tokens=2048
            ),
        ]

        self.model_cache = known_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(known_models)} models from Zhipu AI")
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
        model = model or self.current_model or "glm-4"
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
            "glm-4",
            "glm-4-flash",
            "glm-4-plus",
            "glm-3-turbo",
            "glm-4v",
        ]
