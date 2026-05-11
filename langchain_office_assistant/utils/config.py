from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    agent_model: str = "gpt-4"
    openai_api_key: Optional[str] = None
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