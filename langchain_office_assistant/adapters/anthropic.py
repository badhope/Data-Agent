"""
Anthropic平台适配器
支持Claude-3.5、Claude-3等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class AnthropicAdapter(PlatformAdapter):
    """Anthropic(Claude)平台适配器"""

    def get_platform_name(self) -> str:
        return "Anthropic (Claude)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://api.anthropic.com/v1")

    def get_headers(self) -> Dict[str, str]:
        """获取请求头（Anthropic使用x-api-key）"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "anthropic-dangerous-direct-browser-access": "true"
        }

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取Claude模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        known_models = [
            ModelInfo(
                name="claude-opus-4-5",
                display_name="Claude Opus 4.5",
                description="最强大的Claude模型，擅长复杂分析和创意任务",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning", "function-calling"],
                status="available",
                context_window=200000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="claude-sonnet-4-5",
                display_name="Claude Sonnet 4.5",
                description="平衡性能和成本的模型，适合大多数任务",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning", "function-calling"],
                status="available",
                context_window=200000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="claude-haiku-4",
                display_name="Claude Haiku 4",
                description="快速响应模型，适合简单任务和实时交互",
                provider="anthropic",
                capabilities=["text", "vision", "fast"],
                status="available",
                context_window=200000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="claude-opus-3-5",
                display_name="Claude Opus 3.5",
                description="强大的Claude模型，适合复杂任务",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning", "function-calling"],
                status="available",
                context_window=200000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="claude-sonnet-3-5",
                display_name="Claude Sonnet 3.5",
                description="平衡性能和成本",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning", "function-calling"],
                status="available",
                context_window=200000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="claude-haiku-3-5",
                display_name="Claude Haiku 3.5",
                description="快速轻量模型",
                provider="anthropic",
                capabilities=["text", "vision", "fast"],
                status="available",
                context_window=200000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="claude-opus-3",
                display_name="Claude Opus 3",
                description="Claude 3系列最强大模型",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning"],
                status="available",
                context_window=200000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="claude-sonnet-3",
                display_name="Claude Sonnet 3",
                description="Claude 3平衡模型",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning"],
                status="available",
                context_window=200000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="claude-haiku-3",
                display_name="Claude Haiku 3",
                description="Claude 3快速模型",
                provider="anthropic",
                capabilities=["text", "vision", "fast"],
                status="available",
                context_window=200000,
                max_output_tokens=4096
            ),
        ]

        self.model_cache = known_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(known_models)} Claude models")
        return known_models

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/messages"
            data = {
                "model": model_name,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "say 'OK'"}]
            }

            start_time = time.time()
            response = requests.post(url, headers=self.get_headers(), json=data, timeout=30)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [{}])[0].get("text", "OK")
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
        model = model or self.current_model or "claude-sonnet-4-5"
        url = f"{self.get_api_base()}/messages"

        anthropic_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "assistant":
                role = "assistant"
            elif role == "system":
                continue
            else:
                role = "user"
            anthropic_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        payload = {
            "model": model,
            "messages": anthropic_messages,
            **kwargs
        }

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [{}])[0].get("text", "")
                return {
                    "success": True,
                    "data": {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": content
                            }
                        }],
                        "usage": result.get("usage", {}),
                        "id": result.get("id", ""),
                        "model": result.get("model", model)
                    }
                }
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
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4",
            "claude-opus-3-5",
            "claude-sonnet-3-5",
            "claude-haiku-3-5",
        ]
