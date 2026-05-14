"""
Google Gemini平台适配器
支持Gemini Pro、Ultra等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class GoogleAdapter(PlatformAdapter):
    """Google(Gemini)平台适配器"""

    def get_platform_name(self) -> str:
        return "Google (Gemini)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://generativelanguage.googleapis.com/v1beta")

    def get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json"
        }

    def _get_api_key_param(self) -> str:
        return f"?key={self.api_key}"

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取Gemini模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        try:
            url = f"{self.get_api_base()}/models{self._get_api_key_param()}"
            response = requests.get(url, headers=self.get_headers(), timeout=30)

            if response.status_code != 200:
                logger.error(f"Failed to fetch models: {response.status_code}")
                return self._get_known_models()

            data = response.json()
            models = data.get("models", [])
            all_models = []

            for m in models:
                model_info = ModelInfo(
                    name=m.get("name", "").replace("models/", ""),
                    display_name=self._get_display_name(m.get("name", "")),
                    description=m.get("description", ""),
                    provider="google",
                    capabilities=self._get_capabilities(m),
                    status="available" if m.get("available", []) else "unavailable",
                    context_window=m.get("inputTokenLimit"),
                    max_output_tokens=m.get("outputTokenLimit")
                )
                all_models.append(model_info)

            if not all_models:
                return self._get_known_models()

            self.model_cache = all_models
            self.cache_time = time.time()
            logger.info(f"Loaded {len(all_models)} models from Google Gemini")
            return all_models

        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self._get_known_models()

    def _get_known_models(self) -> List[ModelInfo]:
        """获取已知模型列表"""
        return [
            ModelInfo(
                name="gemini-2.5-pro-preview-06-05",
                display_name="Gemini 2.5 Pro (Preview)",
                description="最新最强Gemini模型，支持多模态",
                provider="google",
                capabilities=["text", "vision", "audio", "video"],
                status="available",
                context_window=1000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-2.0-flash",
                display_name="Gemini 2.0 Flash",
                description="快速响应模型，性价比高",
                provider="google",
                capabilities=["text", "vision", "audio"],
                status="available",
                context_window=1000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                description="轻量快速模型",
                provider="google",
                capabilities=["text", "vision"],
                status="available",
                context_window=1000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-1.5-flash-002",
                display_name="Gemini 1.5 Flash (002)",
                description="Gemini 1.5 Flash更新版本",
                provider="google",
                capabilities=["text", "vision"],
                status="available",
                context_window=1000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                description="高性能Gemini模型，支持超长上下文",
                provider="google",
                capabilities=["text", "vision", "audio"],
                status="available",
                context_window=2000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-1.5-pro-002",
                display_name="Gemini 1.5 Pro (002)",
                description="Gemini 1.5 Pro更新版本",
                provider="google",
                capabilities=["text", "vision", "audio"],
                status="available",
                context_window=2000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-1.5-flash-8b",
                display_name="Gemini 1.5 Flash 8B",
                description="极轻量模型，适合简单任务",
                provider="google",
                capabilities=["text", "vision"],
                status="available",
                context_window=1000000,
                max_output_tokens=8192
            ),
            ModelInfo(
                name="gemini-pro",
                display_name="Gemini Pro",
                description="Gemini基础模型",
                provider="google",
                capabilities=["text", "vision"],
                status="available",
                context_window=30720,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="gemini-pro-vision",
                display_name="Gemini Pro Vision",
                description="支持视觉的Gemini模型",
                provider="google",
                capabilities=["text", "vision"],
                status="available",
                context_window=12288,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="gemini-ultra",
                display_name="Gemini Ultra",
                description="最强大的Gemini模型",
                provider="google",
                capabilities=["text", "vision", "reasoning"],
                status="available",
                context_window=30720,
                max_output_tokens=4096
            ),
        ]

    def _get_display_name(self, model_id: str) -> str:
        """获取模型显示名称"""
        name_map = {
            "gemini-2.5-pro-preview-06-05": "Gemini 2.5 Pro (Preview)",
            "gemini-2.0-flash": "Gemini 2.0 Flash",
            "gemini-1.5-flash": "Gemini 1.5 Flash",
            "gemini-1.5-pro": "Gemini 1.5 Pro",
            "gemini-1.5-flash-8b": "Gemini 1.5 Flash 8B",
            "gemini-pro": "Gemini Pro",
            "gemini-pro-vision": "Gemini Pro Vision",
            "gemini-ultra": "Gemini Ultra",
        }
        return name_map.get(model_id, model_id.replace("-", " ").title())

    def _get_capabilities(self, model_data: Dict) -> List[str]:
        """获取模型能力"""
        caps = ["text"]
        supported_generation_methods = model_data.get("supported_generation_methods", [])

        if "generateContent" in supported_generation_methods:
            caps.append("text")
        if "vision" in str(model_data.get("description", "")).lower():
            caps.append("vision")
        if "audio" in str(model_data.get("description", "")).lower():
            caps.append("audio")

        return caps

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/models/{model_name}:generateContent{self._get_api_key_param()}"
            data = {
                "contents": [{
                    "parts": [{"text": "say 'OK'"}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 10
                }
            }

            start_time = time.time()
            response = requests.post(url, headers=self.get_headers(), json=data, timeout=30)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                content = ""
                if result.get("candidates"):
                    candidate = result["candidates"][0]
                    if candidate.get("content", {}).get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "OK")
                return {
                    "success": True,
                    "model": model_name,
                    "response": content or "OK",
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
        model = model or self.current_model or "gemini-1.5-flash"
        url = f"{self.get_api_base()}/models/{model}:generateContent{self._get_api_key_param()}"

        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "assistant":
                role = "model"
            else:
                role = "user"
            content = msg.get("content", "")
            if isinstance(content, str):
                parts = [{"text": content}]
            else:
                parts = content if isinstance(content, list) else [{"text": str(content)}]
            contents.append({
                "role": role,
                "parts": parts
            })

        generation_config = kwargs.pop("generation_config", {})
        if "max_tokens" in kwargs:
            generation_config["maxOutputTokens"] = kwargs.pop("max_tokens")
        if kwargs:
            generation_config.update(kwargs)

        payload = {
            "contents": contents
        }
        if generation_config:
            payload["generationConfig"] = generation_config

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                content = ""
                if result.get("candidates"):
                    candidate = result["candidates"][0]
                    if candidate.get("content", {}).get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "")
                return {
                    "success": True,
                    "data": {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": content
                            }
                        }],
                        "usage": result.get("usageMetadata", {}),
                        "model": model
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
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-002",
            "gemini-1.5-pro",
            "gemini-1.5-flash-8b",
            "gemini-2.5-pro-preview-06-05",
        ]
