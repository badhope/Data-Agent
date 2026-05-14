"""公共装饰器"""
import logging
from functools import wraps
from fastapi import HTTPException
from database import current_settings

logger = logging.getLogger(__name__)

def require_api_key(func):
    """装饰器：检查API Key是否已配置"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        api_key = current_settings.llm.get("api_key", "") if isinstance(current_settings.llm, dict) else getattr(current_settings.llm, "api_key", "")
        if not api_key:
            raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
        return await func(*args, **kwargs)
    return wrapper

def get_api_key() -> str:
    """获取当前API Key"""
    api_key = current_settings.llm.get("api_key", "") if isinstance(current_settings.llm, dict) else getattr(current_settings.llm, "api_key", "")
    return api_key or ""
