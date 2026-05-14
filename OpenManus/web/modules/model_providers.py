#!/usr/bin/env python3
"""
DATA-AI - 多模型支持系统
支持：本地模型 + 国内厂商 + 国外厂商
"""

import os
import json
import time
import hashlib
import base64
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# ==================== 配置模型 ====================
@dataclass
class ModelConfig:
    name: str
    provider: str
    model_id: str
    api_key: str = ""
    base_url: str = ""
    enabled: bool = True
    is_default: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    extra_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderConfig:
    name: str
    display_name: str
    icon: str
    models: List[str]
    base_url: str
    requires_region: bool = False
    requires_project_id: bool = False
    auth_type: str = "api_key"  # api_key, oauth, secret
    documentation_url: str = ""

# ==================== 厂商配置 ====================
PROVIDERS = {
    # ==================== 国内厂商 ====================
    
    # 百度文心一言
    "baidu_wenxin": ProviderConfig(
        name="baidu_wenxin",
        display_name="百度文心一言",
        icon="🌐",
        models=[
            "ernie-4.0-8k",
            "ernie-4.0-8k-latest",
            "ernie-3.5-8k",
            "ernie-3.5-8k-latest",
            "ernie-speed-8k",
            "ernie-speed-128k",
            "ernie-lite-8k",
            "ernie-lite-8k-latest",
        ],
        base_url="https://aip.baidubce.com/rpc/5.0/pro/advanced",
        requires_region=True,
        documentation_url="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hf1uw2kav"
    ),
    
    # 阿里通义千问
    "aliyun_qwen": ProviderConfig(
        name="aliyun_qwen",
        display_name="阿里云通义千问",
        icon="☁️",
        models=[
            "qwen-max",
            "qwen-max-longcontext",
            "qwen-plus",
            "qwen-turbo",
            "qwen-long",
            "qwen-2-72b-chat",
            "qwen-2-7b-chat",
            "qwen-2-1.8b-chat",
        ],
        base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        requires_region=False,
        documentation_url="https://help.aliyun.com/zh/dashscope/"
    ),
    
    # 腾讯混元
    "tencent_hunyuan": ProviderConfig(
        name="tencent_hunyuan",
        display_name="腾讯混元",
        icon="🐧",
        models=[
            "hunyuan",
            "hunyuan-pro",
            "hunyuan-standard",
            "hunyuan-lite",
            "hunyuan-functioncall",
        ],
        base_url="https://api.hunyuan.cloud.tencent.com/v1",
        requires_region=False,
        requires_project_id=True,
        documentation_url="https://cloud.tencent.com/document/product/1729"
    ),
    
    # 字节豆包
    "bytedance_doubao": ProviderConfig(
        name="bytedance_doubao",
        display_name="字节豆包",
        icon="🎵",
        models=[
            "doubao-pro-32k",
            "doubao-pro-128k",
            "doubao-lite-32k",
            "doubao-lite-4k",
            "doubao-thinking",
        ],
        base_url="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        requires_region=True,
        documentation_url="https://www.volcengine.com/docs/82379/1399008"
    ),
    
    # 智谱 GLM
    "zhipu_glm": ProviderConfig(
        name="zhipu_glm",
        display_name="智谱 GLM",
        icon="🧠",
        models=[
            "glm-4-plus",
            "glm-4",
            "glm-4-flash",
            "glm-4-air",
            "glm-4-airx",
            "glm-3-turbo",
        ],
        base_url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        requires_region=False,
        documentation_url="https://open.bigmodel.cn/doc/api"
    ),
    
    # 月之暗面 Kimi
    "moonshot_kimi": ProviderConfig(
        name="moonshot_kimi",
        display_name="月之暗面 Kimi",
        icon="🌙",
        models=[
            "moonshot-v1-128k",
            "moonshot-v1-32k",
            "moonshot-v1-8k",
        ],
        base_url="https://api.moonshot.cn/v1/chat/completions",
        requires_region=False,
        documentation_url="https://platform.moonshot.cn/docs"
    ),
    
    # 讯飞星火
    "iflytek_spark": ProviderConfig(
        name="iflytek_spark",
        display_name="讯飞星火",
        icon="✨",
        models=[
            "Spark4.0 Ultra",
            "Spark4.0",
            "Spark3.5 Ultra",
            "Spark3.5",
            "Spark2.0",
        ],
        base_url="https://spark-api.xf-yun.com/v3.5/chat",
        requires_region=False,
        requires_project_id=True,
        auth_type="secret",
        documentation_url="https://www.xfyun.cn/doc/tts/online_quickstart/API.html"
    ),
    
    # 商汤日日新
    "sensetime_riri": ProviderConfig(
        name="sensetime_riri",
        display_name="商汤日日新",
        icon="🕐",
        models=[
            "internlm2.5-latest",
            "internlm2-latest",
            "minimax-02",
            "minimax-text-01",
            "sqlcoc",
            "avatar",
        ],
        base_url="https://api.sensetime.com/v1/cv/v1/chat/completions",
        requires_region=False,
        documentation_url="https://api.sensetime.com/docs"
    ),
    
    # MiniMax
    "minimax": ProviderConfig(
        name="minimax",
        display_name="MiniMax",
        icon="🔵",
        models=[
            "abab6-chat",
            "abab5.5-chat",
            "abab5-chat",
        ],
        base_url="https://api.minimax.chat/v1/text/chatcompletion_v2",
        requires_region=False,
        documentation_url="https://www.minimax.io/document/"
    ),
    
    # 深度求索 DeepSeek
    "deepseek": ProviderConfig(
        name="deepseek",
        display_name="深度求索 DeepSeek",
        icon="🔍",
        models=[
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-chat-v2",
            "deepseek-coder-v2",
        ],
        base_url="https://api.deepseek.com/v1/chat/completions",
        requires_region=False,
        documentation_url="https://platform.deepseek.com/docs"
    ),
    
    # ==================== 国外厂商 ====================
    
    # OpenAI
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI",
        icon="🤖",
        models=[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ],
        base_url="https://api.openai.com/v1/chat/completions",
        requires_region=False,
        documentation_url="https://platform.openai.com/docs"
    ),
    
    # Anthropic Claude
    "anthropic": ProviderConfig(
        name="anthropic",
        display_name="Anthropic Claude",
        icon="🧬",
        models=[
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-latest",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        base_url="https://api.anthropic.com/v1/messages",
        requires_region=False,
        auth_type="secret",
        documentation_url="https://docs.anthropic.com/claude/reference"
    ),
    
    # Google Gemini
    "google_gemini": ProviderConfig(
        name="google_gemini",
        display_name="Google Gemini",
        icon="💎",
        models=[
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-pro",
            "gemini-pro-vision",
        ],
        base_url="https://generativelanguage.googleapis.com/v1beta/models",
        requires_region=True,
        documentation_url="https://ai.google.dev/docs"
    ),
    
    # Cohere
    "cohere": ProviderConfig(
        name="cohere",
        display_name="Cohere",
        icon="🌊",
        models=[
            "command-r-plus",
            "command-r",
            "command",
            "command-light",
        ],
        base_url="https://api.cohere.ai/v1/chat",
        requires_region=False,
        documentation_url="https://docs.cohere.com/docs"
    ),
    
    # Mistral AI
    "mistral": ProviderConfig(
        name="mistral",
        display_name="Mistral AI",
        icon="🌬️",
        models=[
            "mistral-large-latest",
            "mistral-small-latest",
            "mistral-nemo",
            "mixtral-8x22b-instruct",
            "mixtral-8x7b-instruct",
        ],
        base_url="https://api.mistral.ai/v1/chat/completions",
        requires_region=False,
        documentation_url="https://docs.mistral.ai/"
    ),
    
    # ==================== 本地模型 ====================
    
    # Ollama
    "ollama": ProviderConfig(
        name="ollama",
        display_name="Ollama 本地模型",
        icon="🏠",
        models=[
            "llama3.1:8b",
            "llama3.1:70b",
            "llama3.1:405b",
            "qwen2.5:7b",
            "qwen2.5:14b",
            "qwen2.5:32b",
            "qwen2.5-coder:7b",
            "qwen2.5-coder:14b",
            "deepseek-coder-v2:16b",
            "codellama:7b",
            "codellama:13b",
            "codellama:34b",
            "mistral:7b",
            "mixtral:8x7b",
            "phi3:14b",
            "gemma2:9b",
            "gemma2:27b",
            "nomic-embed-text",
        ],
        base_url="http://localhost:11434/v1/chat/completions",
        requires_region=False,
        documentation_url="https://github.com/ollama/ollama"
    ),
}

# ==================== API 适配器基类 ====================
class BaseAdapter:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.provider = PROVIDERS.get(config.provider)
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
    
    def _build_headers(self) -> Dict[str, str]:
        raise NotImplementedError

# ==================== OpenAI 兼容格式适配器 ====================
class OpenAICompatibleAdapter(BaseAdapter):
    """适用于 OpenAI、DeepSeek、智谱、Kimi、MiniMax 等兼容 OpenAI 格式的厂商"""
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        import aiohttp
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        data = {
            "model": self.config.model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        if "stream" in kwargs:
            data["stream"] = kwargs["stream"]
        
        # 添加额外参数
        if self.config.extra_params:
            data.update(self.config.extra_params)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.base_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"error": f"API Error {resp.status}: {error_text}"}
                    
                    result = await resp.json()
                    return self._parse_response(result)
        except Exception as e:
            return {"error": str(e)}
    
    def _build_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
    
    def _parse_response(self, result: Dict) -> Dict[str, Any]:
        if "choices" in result:
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result.get("model", self.config.model_id),
                "usage": result.get("usage", {}),
                "id": result.get("id", ""),
            }
        return result

# ==================== 百度文心适配器 ====================
class BaiduWenxinAdapter(BaseAdapter):
    """百度文心一言专用适配器"""
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        import aiohttp
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "assistant":
                role = "assistant"
            elif role == "user":
                role = "user"
            else:
                role = "user"
            formatted_messages.append({
                "role": role,
                "content": msg["content"]
            })
        
        # 构建请求
        access_token = await self._get_access_token()
        url = f"{self.config.base_url}?access_token={access_token}"
        
        data = {
            "model": self.config.model_id,
            "messages": formatted_messages,
            "stream": kwargs.get("stream", False),
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    result = await resp.json()
                    if "error_code" in result:
                        return {"error": f"{result.get('error_code')}: {result.get('error_msg')}"}
                    return self._parse_response(result)
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_access_token(self) -> str:
        """获取百度 access_token"""
        token_cache = getattr(self, '_token_cache', {})
        if token_cache and token_cache.get('expires', 0) > time.time():
            return token_cache['access_token']
        
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.config.api_key,
            "client_secret": self.config.extra_params.get("secret_key", "")
        }
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(token_url, params=params) as resp:
                result = await resp.json()
                self._token_cache = {
                    'access_token': result['access_token'],
                    'expires': time.time() + result.get('expires_in', 2592000) - 300
                }
                return result['access_token']
    
    def _parse_response(self, result: Dict) -> Dict[str, Any]:
        if "result" in result:
            return {
                "content": result["result"],
                "model": self.config.model_id,
                "usage": result.get("usage", {}),
            }
        return result

# ==================== 阿里通义适配器 ====================
class AliyunQwenAdapter(OpenAICompatibleAdapter):
    """阿里云通义千问专用适配器"""
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        import aiohttp
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        data = {
            "model": self.config.model_id,
            "input": {"messages": messages},
            "parameters": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.base_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    result = await resp.json()
                    if "error" in result:
                        return {"error": f"{result['error']['code']}: {result['error']['message']}"}
                    return self._parse_response(result)
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_response(self, result: Dict) -> Dict[str, Any]:
        if "output" in result and "choices" in result["output"]:
            return {
                "content": result["output"]["choices"][0]["message"]["content"],
                "model": result.get("model", self.config.model_id),
                "usage": result.get("usage", {}),
            }
        return result

# ==================== Claude 适配器 ====================
class AnthropicAdapter(BaseAdapter):
    """Anthropic Claude 专用适配器"""
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        import aiohttp
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-dangerous-direct-browser-access": "true"
        }
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if msg["role"] == "system":
                formatted_messages.append({
                    "type": "text",
                    "text": msg["content"]
                })
            else:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        data = {
            "model": self.config.model_id,
            "messages": [m for m in formatted_messages if m.get("role") != "system"],
            "system": next((m["content"] for m in formatted_messages if m.get("role") == "system" and isinstance(m, dict)), None),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.base_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    result = await resp.json()
                    if "error" in result:
                        return {"error": f"{result['error']['type']}: {result['error']['message']}"}
                    return self._parse_response(result)
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_response(self, result: Dict) -> Dict[str, Any]:
        if "content" in result:
            return {
                "content": result["content"][0]["text"],
                "model": result.get("model", self.config.model_id),
                "usage": {
                    "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": result.get("usage", {}).get("output_tokens", 0),
                },
            }
        return result

# ==================== 讯飞星火适配器 ====================
class IFlytekSparkAdapter(BaseAdapter):
    """讯飞星火专用适配器"""
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        import aiohttp
        
        # 讯飞使用特殊认证
        auth_params = await self._generate_auth()
        
        url = f"{self.config.base_url}?{auth_params}"
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        data = {
            "header": {
                "app_id": self.config.extra_params.get("app_id", ""),
            },
            "parameter": {
                "chat": {
                    "domain": self.config.model_id,
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                }
            },
            "payload": {
                "message": {
                    "text": formatted_messages
                }
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    result = await resp.json()
                    if result.get("header", {}).get("code") != 0:
                        return {"error": result.get("header", {}).get("message", "Unknown error")}
                    return self._parse_response(result)
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_auth(self) -> str:
        """生成讯飞认证参数"""
        import base64
        import hmac
        from datetime import datetime
        
        param_dict = self.config.extra_params
        API_KEY = param_dict.get("api_key", "")
        API_SECRET = param_dict.get("api_secret", "")
        
        # 生成 RFC1123 格式的时间戳
        now = datetime.now()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 签名
        signature_origin = f"host: spark-api.xf-yun.com\ndate: {date}\nGET /v3.5/chat HTTP/1.1"
        signature_sha = hmac.new(
            API_SECRET.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        
        authorization_origin = f'Wisedomain="spark", SignatureHeader="host date request-line", Signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        return f"authorization={authorization}&date={date}&host=spark-api.xf-yun.com"
    
    def _parse_response(self, result: Dict) -> Dict[str, Any]:
        choices = result.get("payload", {}).get("choices", {}).get("text", [])
        if choices:
            return {
                "content": choices[0]["content"],
                "model": self.config.model_id,
                "usage": {},
            }
        return result

# ==================== Ollama 适配器 ====================
class OllamaAdapter(BaseAdapter):
    """Ollama 本地模型适配器"""
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        import aiohttp
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        data = {
            "model": self.config.model_id,
            "messages": formatted_messages,
            "stream": kwargs.get("stream", False),
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.base_url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    result = await resp.json()
                    return self._parse_response(result)
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_response(self, result: Dict) -> Dict[str, Any]:
        if "message" in result:
            return {
                "content": result["message"]["content"],
                "model": result.get("model", self.config.model_id),
                "usage": result.get("eval_count", {}),
            }
        return result

# ==================== 适配器工厂 ====================
ADAPTER_MAP = {
    "baidu_wenxin": BaiduWenxinAdapter,
    "aliyun_qwen": AliyunQwenAdapter,
    "anthropic": AnthropicAdapter,
    "iflytek_spark": IFlytekSparkAdapter,
    "ollama": OllamaAdapter,
}

def get_adapter(config: ModelConfig) -> BaseAdapter:
    """获取对应的适配器"""
    adapter_class = ADAPTER_MAP.get(config.provider, OpenAICompatibleAdapter)
    return adapter_class(config)

# ==================== 模型管理器 ====================
class ModelManager:
    def __init__(self, config_path: str = "model_config.json"):
        self.config_path = config_path
        self.models: Dict[str, ModelConfig] = {}
        self.adapters: Dict[str, BaseAdapter] = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for m in data.get("models", []):
                        config = ModelConfig(**m)
                        self.models[config.name] = config
                        self.adapters[config.name] = get_adapter(config)
            except Exception as e:
                print(f"Failed to load config: {e}")
    
    def save_config(self):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            data = {"models": [vars(m) for m in self.models.values()]}
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_model(self, config: ModelConfig):
        """添加模型"""
        self.models[config.name] = config
        self.adapters[config.name] = get_adapter(config)
        self.save_config()
    
    def remove_model(self, name: str):
        """移除模型"""
        if name in self.models:
            del self.models[name]
            del self.adapters[name]
            self.save_config()
    
    def get_default_model(self) -> Optional[ModelConfig]:
        """获取默认模型"""
        for model in self.models.values():
            if model.is_default:
                return model
        return next(iter(self.models.values()), None)
    
    async def chat(self, messages: List[Dict], model_name: str = None, **kwargs) -> Dict[str, Any]:
        """发送聊天请求"""
        if model_name:
            adapter = self.adapters.get(model_name)
        else:
            default = self.get_default_model()
            if default:
                adapter = self.adapters.get(default.name)
            else:
                return {"error": "No model configured"}
        
        if not adapter:
            return {"error": "Model not found"}
        
        return await adapter.chat(messages, **kwargs)
    
    def list_providers(self) -> List[Dict]:
        """列出所有提供商"""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "icon": p.icon,
                "models": p.models,
                "documentation_url": p.documentation_url,
            }
            for p in PROVIDERS.values()
        ]

# ==================== 测试函数 ====================
async def test_all_models():
    """测试所有配置的模型"""
    manager = ModelManager()
    
    for name, model in manager.models.items():
        print(f"\n{'='*50}")
        print(f"Testing: {name} ({model.provider})")
        print(f"Model: {model.model_id}")
        
        try:
            result = await manager.chat([
                {"role": "user", "content": "Hello, say 'OK' in one word"}
            ], name)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Response: {result.get('content', 'No content')}")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("Available Providers:")
    for name, provider in PROVIDERS.items():
        print(f"\n{provider.icon} {provider.display_name} ({name})")
        print(f"   Models: {len(provider.models)}")
        print(f"   Base URL: {provider.base_url}")
        print(f"   Doc: {provider.documentation_url}")
