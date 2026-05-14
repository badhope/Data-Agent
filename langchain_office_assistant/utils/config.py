from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path


def find_env_file():
    current = Path.cwd()
    project_root = Path(__file__).parent.parent
    search_paths = [
        current,
        current.parent,
        project_root,
        project_root.parent,
    ]
    for path in search_paths:
        env_path = path / ".env"
        if env_path.exists():
            return str(env_path)
    return None


env_file_path = find_env_file()

class Config(BaseSettings):
    if env_file_path:
        model_config = SettingsConfigDict(env_file=env_file_path, env_file_encoding="utf-8")
    else:
        model_config = SettingsConfigDict(env_file_encoding="utf-8")

    agent_model: str = "qwen-plus"
    default_platform: str = "dashscope"
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ollama_base_url: str = "http://localhost:11434"

    openai_api_key_alt: Optional[str] = None
    openai_api_base_alt: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-01"

    zhipu_api_key: Optional[str] = None
    zhipu_api_base: Optional[str] = None

    spark_api_key: Optional[str] = None
    spark_api_secret: Optional[str] = None
    spark_api_base: Optional[str] = None

    ernie_api_key: Optional[str] = None
    ernie_api_secret: Optional[str] = None
    ernie_api_base: Optional[str] = None

    doubao_api_key: Optional[str] = None
    doubao_api_base: Optional[str] = None

    custom_api_key: Optional[str] = None
    custom_api_base: Optional[str] = None
    custom_platform_name: Optional[str] = None
    custom_default_model: Optional[str] = None

    redis_url: str = "redis://localhost:6379"
    vector_db_url: str = "http://localhost:19530"
    vector_db_type: str = "faiss"

    log_level: str = "INFO"
    debug_mode: bool = False

    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    def get_platform_config(self, platform: str) -> dict:
        platform = platform.lower()
        configs = {
            "dashscope": {
                "api_key": self.openai_api_key,
                "api_base": self.openai_api_base or "https://dashscope.aliyuncs.com"
            },
            "openai": {
                "api_key": self.openai_api_key_alt or self.openai_api_key,
                "api_base": self.openai_api_base_alt or "https://api.openai.com/v1"
            },
            "anthropic": {
                "api_key": self.anthropic_api_key,
                "api_base": "https://api.anthropic.com/v1"
            },
            "gemini": {
                "api_key": self.gemini_api_key,
                "api_base": "https://generativelanguage.googleapis.com/v1beta"
            },
            "azure": {
                "api_key": self.azure_openai_key,
                "api_base": self.azure_openai_endpoint,
                "api_version": self.azure_openai_api_version
            },
            "zhipu": {
                "api_key": self.zhipu_api_key,
                "api_base": self.zhipu_api_base or "https://open.bigmodel.cn/api/paas/v4"
            },
            "spark": {
                "api_key": self.spark_api_key,
                "api_secret": self.spark_api_secret,
                "api_base": self.spark_api_base or "https://spark-api.xf-yun.com/v3.5/chat"
            },
            "ernie": {
                "api_key": self.ernie_api_key,
                "secret_key": self.ernie_api_secret,
                "api_base": self.ernie_api_base or "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
            },
            "doubao": {
                "api_key": self.doubao_api_key,
                "api_base": self.doubao_api_base or "https://ark.cn-beijing.volces.com/api/v3"
            },
            "custom": {
                "api_key": self.custom_api_key,
                "api_base": self.custom_api_base or "http://localhost:8080/v1",
                "platform_name": self.custom_platform_name,
                "default_model": self.custom_default_model
            },
        }
        return configs.get(platform, {})

    def is_platform_configured(self, platform: str) -> bool:
        platform = platform.lower()
        cfg = self.get_platform_config(platform)
        if platform in ["spark", "ernie"]:
            return bool(cfg.get("api_key") and (cfg.get("api_secret") or cfg.get("secret_key")))
        return bool(cfg.get("api_key"))

config = Config()

if config.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", config.openai_api_key)
if config.openai_api_base:
    os.environ.setdefault("OPENAI_API_BASE", config.openai_api_base)
