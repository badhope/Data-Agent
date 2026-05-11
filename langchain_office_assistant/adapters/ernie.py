"""
文心一言 (ERNIE)平台适配器
支持 ERNIE-4.0、ERNIE-3.5 等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class ErnieAdapter(PlatformAdapter):
    """文心一言 (ERNIE)平台适配器"""

    def get_platform_name(self) -> str:
        return "文心一言 (ERNIE)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat")

    def _get_access_token(self) -> Optional[str]:
        """获取百度文心Access Token"""
        api_key = self.config.get("api_key", self.api_key)
        secret_key = self.config.get("secret_key", "")
        
        if not secret_key:
            return None

        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        try:
            response = requests.get(token_url, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get("access_token")
        except Exception as e:
            logger.error(f"获取Access Token失败: {e}")
        return None

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取文心一言模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        known_models = [
            ModelInfo(
                name="ernie-4.0-8k",
                display_name="ERNIE-4.0 8K",
                description="文心4.0旗舰版，8K上下文",
                provider="baidu",
                capabilities=["文本生成", "函数调用"],
                status="available",
                context_window=8192,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="ernie-4.0-turbo-8k",
                display_name="ERNIE-4.0 Turbo 8K",
                description="文心4.0 Turbo，速度更快",
                provider="baidu",
                capabilities=["文本生成", "函数调用"],
                status="available",
                context_window=8192,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="ernie-4.0-turbo-128k",
                display_name="ERNIE-4.0 Turbo 128K",
                description="文心4.0 Turbo，超长上下文128K",
                provider="baidu",
                capabilities=["文本生成", "长上下文", "函数调用"],
                status="available",
                context_window=128000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="ernie-3.5-8k",
                display_name="ERNIE-3.5 8K",
                description="文心3.5稳定版",
                provider="baidu",
                capabilities=["文本生成", "函数调用"],
                status="available",
                context_window=8192,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="ernie-lite-8k",
                display_name="ERNIE Lite 8K",
                description="文心轻量版，性价比高",
                provider="baidu",
                capabilities=["文本生成"],
                status="available",
                context_window=8192,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="ernie-speed-128k",
                display_name="ERNIE Speed 128K",
                description="文心速度版，128K长上下文",
                provider="baidu",
                capabilities=["文本生成", "长上下文"],
                status="available",
                context_window=128000,
                max_output_tokens=4096
            ),
        ]

        self.model_cache = known_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(known_models)} models from ERNIE")
        return known_models

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "model": model_name,
                    "error": "获取Access Token失败",
                    "error_detail": "请检查 API Key 和 Secret Key 是否正确",
                    "platform": self.get_platform_name()
                }

            url = f"{self.get_api_base()}/{model_name}?access_token={access_token}"
            data = {
                "messages": [{"role": "user", "content": "say 'OK'"}]
            }

            start_time = time.time()
            response = requests.post(url, json=data, timeout=30)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                if "error_code" not in result:
                    content = result.get("result", "OK")
                    return {
                        "success": True,
                        "model": model_name,
                        "response": content,
                        "duration_ms": int(duration),
                        "platform": self.get_platform_name()
                    }
                else:
                    error_msg = result.get("error_msg", "请求失败")
                    return {
                        "success": False,
                        "model": model_name,
                        "error": self._parse_error(error_msg),
                        "error_detail": error_msg,
                        "platform": self.get_platform_name()
                    }
            else:
                return {
                    "success": False,
                    "model": model_name,
                    "error": "请求失败",
                    "error_detail": f"HTTP {response.status_code}",
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
        model = model or self.current_model or "ernie-4.0-8k"
        access_token = self._get_access_token()
        
        if not access_token:
            return {"success": False, "error": "获取Access Token失败"}

        url = f"{self.get_api_base()}/{model}?access_token={access_token}"
        payload = {
            "messages": messages,
            **kwargs
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                if "error_code" not in result:
                    return {"success": True, "data": result}
                else:
                    return {
                        "success": False,
                        "error": result.get("error_msg", "请求失败"),
                        "raw_response": response.text
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "raw_response": response.text
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recommended_models(self) -> List[str]:
        """获取推荐模型列表"""
        return [
            "ernie-4.0-8k",
            "ernie-4.0-turbo-8k",
            "ernie-4.0-turbo-128k",
            "ernie-3.5-8k",
            "ernie-lite-8k",
            "ernie-speed-128k",
        ]
