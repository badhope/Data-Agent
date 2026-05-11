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
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ollama_base_url: str = "http://localhost:11434"

    redis_url: str = "redis://localhost:6379"
    vector_db_url: str = "http://localhost:19530"
    vector_db_type: str = "faiss"

    log_level: str = "INFO"
    debug_mode: bool = False

    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

config = Config()

if config.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", config.openai_api_key)
if config.openai_api_base:
    os.environ.setdefault("OPENAI_API_BASE", config.openai_api_base)
