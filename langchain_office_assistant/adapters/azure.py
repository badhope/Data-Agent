"""
Azure OpenAI平台适配器
支持Azure部署的GPT-4、GPT-3.5等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class AzureAdapter(PlatformAdapter):
    """Azure OpenAI平台适配器"""

    def get_platform_name(self) -> str:
        return "Azure OpenAI"

    def get_api_base(self) -> str:
        base = self.config.get("api_base", "")
        if not base:
            raise ValueError("Azure OpenAI requires api_base (deployment URL)")
        return base.rstrip("/")

    def get_api_version(self) -> str:
        return self.config.get("api_version", "2024-02-01")

    def get_headers(self) -> Dict[str, str]:
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取Azure OpenAI模型列表（需要手动配置）"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        configured_models = self.config.get("models", [])
        if configured_models:
            all_models = []
            for m in configured_models:
                if isinstance(m, str):
                    model_info = ModelInfo(
                        name=m,
                        display_name=m,
                        description=f"Azure OpenAI {m}模型",
                        provider="azure",
                        capabilities=["text"],
                        status="available"
                    )
                else:
                    model_info = ModelInfo(
                        name=m.get("name", ""),
                        display_name=m.get("display_name", m.get("name", "")),
                        description=m.get("description", ""),
                        provider="azure",
                        capabilities=m.get("capabilities", ["text"]),
                        status="available"
                    )
                all_models.append(model_info)
        else:
            all_models = [
                ModelInfo(
                    name="gpt-4",
                    display_name="GPT-4",
                    description="Azure OpenAI GPT-4模型",
                    provider="azure",
                    capabilities=["text", "vision", "function-calling"],
                    status="available",
                    context_window=128000
                ),
                ModelInfo(
                    name="gpt-4-turbo",
                    display_name="GPT-4 Turbo",
                    description="Azure OpenAI GPT-4 Turbo模型",
                    provider="azure",
                    capabilities=["text", "vision", "function-calling"],
                    status="available",
                    context_window=128000
                ),
                ModelInfo(
                    name="gpt-4o",
                    display_name="GPT-4o",
                    description="Azure OpenAI GPT-4o多模态模型",
                    provider="azure",
                    capabilities=["text", "vision", "audio"],
                    status="available",
                    context_window=128000
                ),
                ModelInfo(
                    name="gpt-35-turbo",
                    display_name="GPT-3.5 Turbo",
                    description="Azure OpenAI GPT-3.5 Turbo模型",
                    provider="azure",
                    capabilities=["text", "function-calling"],
                    status="available",
                    context_window=16385
                ),
            ]

        self.model_cache = all_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(all_models)} Azure OpenAI models")
        return all_models

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/chat/completions?api-version={self.get_api_version()}"
            data = {
                "messages": [{"role": "user", "content": "say 'OK'"}],
                "max_tokens": 10
            }

            headers = self.get_headers()
            if model_name and model_name != "deployment":
                data["model"] = model_name

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
        url = f"{self.get_api_base()}/chat/completions?api-version={self.get_api_version()}"

        payload = {
            "messages": messages,
            **kwargs
        }

        if model:
            payload["model"] = model

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
            "gpt-4-turbo",
            "gpt-4",
            "gpt-35-turbo",
        ]
