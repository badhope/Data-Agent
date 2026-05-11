"""
模型管理器 - 动态管理和选择模型
支持阿里百炼平台的482+个模型
"""
import requests
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import time
import os
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

class ModelInfo(BaseModel):
    name: str
    display_name: str
    description: str
    provider: str = ""
    capabilities: List[str] = []
    status: str = "unknown"

class ModelManager:
    def __init__(self, api_key: str, api_base: str = "https://dashscope.aliyuncs.com"):
        self.api_key = api_key
        self.api_base = api_base
        self.current_model = None
        self.model_cache = []
        self.cache_time = 0
        self.total_models = 0

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取所有模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        try:
            all_models = []
            page = 1
            page_size = 100

            while True:
                url = f"{self.api_base}/api/v1/models?page_no={page}&page_size={page_size}"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code != 200:
                    logger.error(f"Failed to fetch models: {response.status_code}")
                    break

                data = response.json()
                output = data.get("output", {})
                models = output.get("models", [])

                if self.total_models == 0:
                    self.total_models = output.get("total", 0)

                for m in models:
                    model_info = ModelInfo(
                        name=m.get("model", ""),
                        display_name=m.get("name", m.get("model", "")),
                        description=m.get("description", ""),
                        provider=m.get("provider", ""),
                        capabilities=m.get("capabilities", []),
                        status="available"
                    )
                    all_models.append(model_info)

                if len(all_models) >= self.total_models:
                    break

                page += 1

            self.model_cache = all_models
            self.cache_time = time.time()
            return all_models

        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return self.model_cache if self.model_cache else []

    def get_available_models(self) -> List[ModelInfo]:
        """获取可用模型列表（按类型分类）"""
        models = self.list_models()

        categorized = {
            "text": [],
            "vision": [],
            "image": [],
            "video": [],
            "audio": [],
            "other": []
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

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型是否可用"""
        try:
            url = f"{self.api_base}/compatible-mode/v1/chat/completions"
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
                    "duration_ms": int(duration)
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)

                if "free tier" in error_msg.lower() or "quota" in error_msg.lower():
                    return {
                        "success": False,
                        "model": model_name,
                        "error": "配额不足或免费额度用尽",
                        "error_detail": error_msg
                    }
                elif "not exist" in error_msg.lower() or "404" in error_msg:
                    return {
                        "success": False,
                        "model": model_name,
                        "error": "模型不存在",
                        "error_detail": error_msg
                    }
                elif "stream" in error_msg.lower():
                    return {
                        "success": False,
                        "model": model_name,
                        "error": "该模型仅支持流式输出",
                        "error_detail": error_msg
                    }
                else:
                    return {
                        "success": False,
                        "model": model_name,
                        "error": "模型调用失败",
                        "error_detail": error_msg
                    }

        except Exception as e:
            return {
                "success": False,
                "model": model_name,
                "error": "请求异常",
                "error_detail": str(e)
            }

    def set_model(self, model_name: str) -> bool:
        """设置当前使用的模型"""
        result = self.test_model(model_name)
        if result["success"]:
            self.current_model = model_name
            logger.info(f"Model set to: {model_name}")
            return True
        return False

    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.current_model

    def search_models(self, keyword: str) -> List[ModelInfo]:
        """搜索模型"""
        models = self.list_models()
        keyword_lower = keyword.lower()

        results = []
        for m in models:
            if (keyword_lower in m.name.lower() or
                keyword_lower in m.display_name.lower() or
                keyword_lower in m.description.lower()):
                results.append(m)

        return results[:50]

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表（优先选择可用模型）"""
        return [
            "qwen3.6-plus",
            "qwen3.6-flash",
            "qwen-flash",
            "qwen3.5-plus",
            "qwen3.5-flash",
            "qwen-plus",
            "qwen-turbo",
            "qwen-max",
        ]

    def test_all_recommended(self) -> Dict[str, Any]:
        """测试所有推荐模型并返回可用列表"""
        results = {}
        for model in self.get_recommended_models():
            result = self.test_model(model)
            results[model] = result
            time.sleep(0.3)

        available = [m for m, r in results.items() if r.get("success")]
        unavailable = [m for m, r in results.items() if not r.get("success")]

        return {
            "available": available,
            "unavailable": unavailable,
            "details": results,
            "total_available": len(available)
        }

def create_model_manager(api_key: str = None, api_base: str = "https://dashscope.aliyuncs.com") -> ModelManager:
    """创建模型管理器"""
    if not api_key:
        from langchain_office_assistant.utils.config import config
        api_key = config.openai_api_key
        api_base = config.openai_api_base

    return ModelManager(api_key, api_base)
