"""
OpenAI平台适配器
支持GPT-4、GPT-3.5等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class OpenAIAdapter(PlatformAdapter):
    """OpenAI平台适配器"""

    def get_platform_name(self) -> str:
        return "OpenAI"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://api.openai.com/v1")

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取OpenAI模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        try:
            url = f"{self.get_api_base()}/models"
            response = requests.get(url, headers=self.get_headers(), timeout=30)

            if response.status_code != 200:
                logger.error(f"Failed to fetch models: {response.status_code}")
                return self.model_cache if self.model_cache else []

            data = response.json()
            models = data.get("data", [])
            all_models = []

            for m in models:
                model_id = m.get("id", "")
                owned_by = m.get("owned_by", "")

                context_window = m.get("context_window")
                if context_window is None:
                    context_window = m.get("max_tokens")

                display_name = self._get_display_name(model_id)
                description = self._get_description(model_id)

                model_info = ModelInfo(
                    name=model_id,
                    display_name=display_name,
                    description=description,
                    provider=owned_by,
                    capabilities=self._get_capabilities(model_id),
                    status="available" if m.get("ready", True) else "unavailable",
                    context_window=context_window,
                    max_output_tokens=m.get("max_output_tokens")
                )
                all_models.append(model_info)

            self.model_cache = all_models
            self.cache_time = time.time()
            logger.info(f"Loaded {len(all_models)} models from OpenAI")
            return all_models

        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self.model_cache if self.model_cache else []

    def _get_display_name(self, model_id: str) -> str:
        """获取模型显示名称"""
        name_map = {
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-4-turbo-preview": "GPT-4 Turbo Preview",
            "gpt-4": "GPT-4",
            "gpt-4-32k": "GPT-4 32K",
            "gpt-3.5-turbo": "GPT-3.5 Turbo",
            "gpt-3.5-turbo-16k": "GPT-3.5 Turbo 16K",
            "o1-preview": "o1 Preview",
            "o1-mini": "o1 Mini",
            "o3": "o3",
            "o3-mini": "o3 Mini",
            "o4-mini": "o4 Mini",
            "gpt-4.5": "GPT-4.5",
            "gpt-4.5-turbo": "GPT-4.5 Turbo",
        }
        return name_map.get(model_id, model_id.replace("-", " ").title())

    def _get_description(self, model_id: str) -> str:
        """获取模型描述"""
        desc_map = {
            "gpt-4o": "最新最强多模态模型，支持文本、图像、音频",
            "gpt-4o-mini": "轻量级多模态模型，性价比高",
            "gpt-4-turbo": "高性能GPT-4，更快更便宜",
            "gpt-4": "强大的GPT-4模型，支持长上下文",
            "gpt-3.5-turbo": "快速响应，适合简单任务",
            "o1-preview": "新一代推理模型，擅长复杂问题",
            "o1-mini": "轻量级推理模型",
            "o3": "最新推理模型，超越o1",
            "o3-mini": "o3轻量版",
            "o4-mini": "o4轻量多模态版",
        }
        return desc_map.get(model_id, f"OpenAI {model_id}模型")

    def _get_capabilities(self, model_id: str) -> List[str]:
        """获取模型能力"""
        caps = ["text"]
        if "vision" in model_id or "4o" in model_id or "4-turbo" in model_id:
            caps.append("vision")
        if "16k" in model_id or "32k" in model_id or "turbo" in model_id or "4" in model_id:
            caps.append("long-context")
        if "o1" in model_id or "o3" in model_id or "o4" in model_id:
            caps.append("reasoning")
        return caps

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/chat/completions"
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": "say 'OK'"}],
                "max_tokens": 10
            }

            start_time = time.time()
            response = requests.post(url, headers=self.get_headers(), json=data, timeout=30)
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
        model = model or self.current_model or "gpt-3.5-turbo"
        url = f"{self.get_api_base()}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=120)
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
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
            "o3",
            "o3-mini",
        ]
