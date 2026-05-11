"""
阿里百炼(DashScope)平台适配器
支持482+模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class DashScopeAdapter(PlatformAdapter):
    """阿里百炼平台适配器"""

    def get_platform_name(self) -> str:
        return "阿里百炼 (DashScope)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://dashscope.aliyuncs.com")

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取阿里百炼所有模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        try:
            all_models = []
            page = 1
            page_size = 100
            total = 0

            while True:
                url = f"{self.get_api_base()}/api/v1/models?page_no={page}&page_size={page_size}"
                response = requests.get(url, headers=self.get_headers(), timeout=30)

                if response.status_code != 200:
                    logger.error(f"Failed to fetch models: {response.status_code}")
                    break

                data = response.json()
                output = data.get("output", {})
                models = output.get("models", [])
                total = output.get("total", total)

                for m in models:
                    model_info = ModelInfo(
                        name=m.get("model", ""),
                        display_name=m.get("name", m.get("model", "")),
                        description=m.get("description", ""),
                        provider=m.get("provider", "aliyun"),
                        capabilities=m.get("capabilities", []),
                        status="available"
                    )
                    all_models.append(model_info)

                if len(all_models) >= total:
                    break

                page += 1

            self.model_cache = all_models
            self.cache_time = time.time()
            logger.info(f"Loaded {len(all_models)} models from DashScope")
            return all_models

        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self.model_cache if self.model_cache else []

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            url = f"{self.get_api_base()}/compatible-mode/v1/chat/completions"
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
        model = model or self.current_model or "qwen-plus"
        url = f"{self.get_api_base()}/compatible-mode/v1/chat/completions"

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
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen3.6-plus",
            "qwen3.6-flash",
            "qwen3.5-plus",
            "qwen3.5-flash",
            "qwen-flash",
            "qwq-32b",
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
            "qwen2-72b-instruct",
            "qwen2-7b-instruct",
            "qwen-audio-chat",
        ]

    def get_available_models(self) -> Dict[str, List[ModelInfo]]:
        """获取可用模型（按类型分类）"""
        models = self.list_models()
        categorized = {
            "text": [], "vision": [], "image": [],
            "video": [], "audio": [], "other": []
        }

        for m in models:
            caps = m.capabilities
            if "VG" in caps:
                categorized["video"].append(m)
            elif "IG" in caps:
                categorized["image"].append(m)
            elif "VU" in caps:
                categorized["vision"].append(m)
            elif "AU" in caps:
                categorized["audio"].append(m)
            elif any(c in caps for c in ["TG", "Reasoning", "function-calling"]):
                categorized["text"].append(m)
            else:
                categorized["other"].append(m)

        return categorized
