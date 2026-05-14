"""
讯飞星火 (iFlyTek Spark)平台适配器
支持 Spark-4.0 Ultra、Spark-3.5 等模型
"""
from typing import List, Dict, Optional, Any
import requests
import time
import logging
import hmac
import hashlib
import base64
import json
from datetime import datetime
from urllib.parse import urlparse, urlencode
from .base import PlatformAdapter, ModelInfo

logger = logging.getLogger(__name__)


class SparkAdapter(PlatformAdapter):
    """讯飞星火 (iFlyTek Spark)平台适配器"""

    def get_platform_name(self) -> str:
        return "讯飞星火 (iFlyTek Spark)"

    def get_api_base(self) -> str:
        return self.config.get("api_base", "https://spark-api.xf-yun.com/v3.5/chat")

    def _generate_auth_url(self, url: str, api_key: str, api_secret: str) -> str:
        """生成讯飞星火鉴权URL"""
        parse_result = urlparse(url)
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature_origin = f"host: {parse_result.netloc}\n"
        signature_origin += f"date: {date}\n"
        signature_origin += f"GET {parse_result.path} HTTP/1.1"
        
        signature_sha = hmac.new(
            api_secret.encode('utf-8'), 
            signature_origin.encode('utf-8'), 
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": parse_result.netloc
        }
        
        return f"{url}?{urlencode(v)}"

    def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """获取讯飞星火模型列表"""
        if not force_refresh and self.model_cache and time.time() - self.cache_time < 3600:
            return self.model_cache

        known_models = [
            ModelInfo(
                name="spark-4.0-ultra",
                display_name="Spark 4.0 Ultra",
                description="最新旗舰版，强大的理解和生成能力",
                provider="iflytek",
                capabilities=["文本生成", "长上下文", "函数调用", "多模态"],
                status="available",
                context_window=8192,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="spark-3.5-max",
                display_name="Spark 3.5 Max",
                description="平衡能力和性能的版本",
                provider="iflytek",
                capabilities=["文本生成", "长上下文", "函数调用"],
                status="available",
                context_window=128000,
                max_output_tokens=4096
            ),
            ModelInfo(
                name="spark-3.5-pro",
                display_name="Spark 3.5 Pro",
                description="专业版，适合一般任务",
                provider="iflytek",
                capabilities=["文本生成", "长上下文"],
                status="available",
                context_window=8192,
                max_output_tokens=2048
            ),
            ModelInfo(
                name="spark-lite",
                display_name="Spark Lite",
                description="轻量版，速度快成本低",
                provider="iflytek",
                capabilities=["文本生成"],
                status="available",
                context_window=4096,
                max_output_tokens=2048
            ),
        ]

        self.model_cache = known_models
        self.cache_time = time.time()
        logger.info(f"Loaded {len(known_models)} models from iFlyTek Spark")
        return known_models

    def test_model(self, model_name: str) -> Dict[str, Any]:
        """测试模型可用性"""
        try:
            api_key = self.config.get("api_key", self.api_key)
            api_secret = self.config.get("api_secret", "")
            
            if not api_secret:
                return {
                    "success": False,
                    "model": model_name,
                    "error": "需要配置 API Secret",
                    "error_detail": "讯飞星火需要同时提供 API Key 和 API Secret",
                    "platform": self.get_platform_name()
                }

            url = self.get_api_base()
            auth_url = self._generate_auth_url(url, api_key, api_secret)
            
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": "say 'OK'"}]
            }

            start_time = time.time()
            response = requests.post(auth_url, json=data, timeout=30)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                if result.get("code", -1) == 0:
                    choices = result.get("choices", [{}])
                    content = choices[0].get("message", {}).get("content", "OK")
                    return {
                        "success": True,
                        "model": model_name,
                        "response": content,
                        "duration_ms": int(duration),
                        "platform": self.get_platform_name()
                    }
                else:
                    error_msg = result.get("message", "请求失败")
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
        model = model or self.current_model or "spark-3.5-max"
        api_key = self.config.get("api_key", self.api_key)
        api_secret = self.config.get("api_secret", "")
        
        if not api_secret:
            return {"success": False, "error": "需要配置 API Secret"}

        url = self.get_api_base()
        auth_url = self._generate_auth_url(url, api_key, api_secret)
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        try:
            response = requests.post(auth_url, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                if result.get("code", -1) == 0:
                    return {"success": True, "data": result}
                else:
                    return {
                        "success": False,
                        "error": result.get("message", "请求失败"),
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
            "spark-4.0-ultra",
            "spark-3.5-max",
            "spark-3.5-pro",
            "spark-lite",
        ]
