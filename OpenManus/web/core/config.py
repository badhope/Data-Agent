"""
Configuration for Web Application
"""
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

class AppSettings(BaseSettings):
    """应用设置"""
    app_name: str = "DATA-AI - 万能智能助手"
    app_version: str = "2.0.0"
    debug: bool = True
    api_prefix: str = "/api/v1"
    
    data_dir: Path = BASE_DIR / "data"
    
    class Config:
        env_prefix = "DATA_AI_"

_settings = AppSettings()

def get_settings() -> AppSettings:
    return _settings
