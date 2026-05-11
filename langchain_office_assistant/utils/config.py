from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path

def find_env_file():
    """Find .env file in current directory or parent directories."""
    current = Path.cwd()
    for path in [current, current.parent, Path(__file__).parent]:
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
        """获取指定平台的配置"""
        platform = platform.lower()

        if platform == "dashscope":
            return {
                "api_key": self.openai_api_key,
                "api_base": self.openai_api_base or "https://dashscope.aliyuncs.com"
            }
        elif platform == "openai":
            return {
                "api_key": self.openai_api_key_alt or self.openai_api_key,
                "api_base": self.openai_api_base_alt or "https://api.openai.com/v1"
            }
        elif platform == "anthropic":
            return {
                "api_key": self.anthropic_api_key,
                "api_base": "https://api.anthropic.com/v1"
            }
        elif platform == "gemini":
            return {
                "api_key": self.gemini_api_key,
                "api_base": "https://generativelanguage.googleapis.com/v1beta"
            }
        elif platform == "azure":
            return {
                "api_key": self.azure_openai_key,
                "api_base": self.azure_openai_endpoint,
                "api_version": self.azure_openai_api_version
            }
        else:
            return {}

    def is_platform_configured(self, platform: str) -> bool:
        """检查平台是否已配置"""
        platform = platform.lower()
        config = self.get_platform_config(platform)
        return bool(config.get("api_key"))

config = Config()

if config.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", config.openai_api_key)
if config.openai_api_base:
    os.environ.setdefault("OPENAI_API_BASE", config.openai_api_base)
