"""
模型管理器 - 动态管理和选择模型
支持阿里百炼平台的多个模型
"""
import requests
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import time
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

class ModelInfo(BaseModel):
    name: str
    display_name: str
    description: str
    status: str = "available"

class ModelManager:
    def __init__(self, api_key: str, api_base: str = "https://dashscope.aliyuncs.com"):
        self.api_key = api_key
        self.api_base = api_base
        self.current_model = None
        self.model_cache = {}

    def list_models(self) -> List[ModelInfo]:
        """获取模型列表"""
        cached_models = self._get_cached_models()
        if cached_models:
            return cached_models

        try:
            url = f"{self.api_base}/api/v1/models"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                models = []

                if "data" in data:
                    for model in data["data"]:
                        model_info = ModelInfo(
                            name=model.get("id", ""),
                            display_name=self._get_display_name(model.get("id", "")),
                            description=self._get_description(model.get("id", "")),
                            status=model.get("status", "available")
                        )
                        models.append(model_info)

                self._cache_models(models)
                return models
            else:
                logger.warning(f"Failed to fetch models: {response.status_code}")
                return self._get_default_models()

        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self._get_default_models()

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型是否可用"""
        try:
            import openai
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )

            start_time = time.time()
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
                max_tokens=10,
                temperature=0
            )
            duration = (time.time() - start_time) * 1000

            return {
                "success": True,
                "model": model_name,
                "response": response.choices[0].message.content,
                "duration_ms": int(duration),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                }
            }

        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "quota" in error_msg.lower():
                return {
                    "success": False,
                    "model": model_name,
                    "error": "配额不足或账户限制",
                    "error_detail": error_msg
                }
            elif "404" in error_msg or "does not exist" in error_msg.lower():
                return {
                    "success": False,
                    "model": model_name,
                    "error": "模型不存在",
                    "error_detail": error_msg
                }
            else:
                return {
                    "success": False,
                    "model": model_name,
                    "error": "模型调用失败",
                    "error_detail": error_msg
                }

    def set_model(self, model_name: str) -> bool:
        """设置当前使用的模型"""
        result = self.test_model(model_name)
        if result["success"]:
            self.current_model = model_name
            logger.info(f"Model set to: {model_name}")
            return True
        else:
            logger.error(f"Failed to set model {model_name}: {result.get('error')}")
            return False

    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.current_model

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表"""
        return [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen-max-longcontext",
            "qwen2-72b-instruct",
            "qwen2-7b-instruct",
            "qwen-audio-turbo",
            "qwen-vl-plus",
            "qwen-vl-max",
        ]

    def search_model(self, query: str) -> List[ModelInfo]:
        """搜索模型"""
        all_models = self.list_models()
        query_lower = query.lower()

        results = []
        for model in all_models:
            if (query_lower in model.name.lower() or
                query_lower in model.display_name.lower() or
                query_lower in model.description.lower()):
                results.append(model)

        if not results:
            for model in all_models:
                if any(keyword in model.name.lower() for keyword in query_lower.split()):
                    results.append(model)

        return results[:20]

    def _get_display_name(self, model_name: str) -> str:
        """获取模型的显示名称"""
        display_names = {
            "qwen-max": "Qwen Max (最强推理)",
            "qwen-plus": "Qwen Plus (增强版)",
            "qwen-turbo": "Qwen Turbo (快速响应)",
            "qwen2": "Qwen 2 (新一代开源)",
        }

        for key, name in display_names.items():
            if key in model_name.lower():
                return name

        return model_name

    def _get_description(self, model_name: str) -> str:
        """获取模型描述"""
        descriptions = {
            "max": "最强推理能力，适合复杂任务",
            "plus": "增强版，性价比高",
            "turbo": "快速响应，适合简单任务",
            "vl": "视觉语言模型，支持图片理解",
            "audio": "音频处理模型",
            "longcontext": "长文本处理",
        }

        for key, desc in descriptions.items():
            if key in model_name.lower():
                return desc

        return "通用模型"

    def _get_default_models(self) -> List[ModelInfo]:
        """获取默认模型列表（当API不可用时）"""
        default_models = [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen-max-longcontext",
            "qwen2-72b-instruct",
            "qwen2-57b-a14b-instruct",
            "qwen2-7b-instruct",
            "qwen2-1.5b-instruct",
            "qwen2-0.5b-instruct",
            "qwen-audio-turbo",
            "qwen-audio",
            "qwen-vl-plus",
            "qwen-vl-max",
            "qwen-math-plus",
            "qwen-math",
        ]

        return [
            ModelInfo(
                name=model,
                display_name=self._get_display_name(model),
                description=self._get_description(model)
            )
            for model in default_models
        ]

    def _cache_models(self, models: List[ModelInfo]):
        """缓存模型列表"""
        self.model_cache = {model.name: model for model in models}
        self.cache_time = time.time()

    def _get_cached_models(self) -> Optional[List[ModelInfo]]:
        """获取缓存的模型列表"""
        if hasattr(self, 'cache_time'):
            if time.time() - self.cache_time < 3600:
                return list(self.model_cache.values())
        return None

def create_model_manager(api_key: str, api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1") -> ModelManager:
    """创建模型管理器"""
    return ModelManager(api_key, api_base)
