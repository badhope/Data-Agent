"""
Settings API Router
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from web.models import Settings
from web.storage import get_settings, save_settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.get("")
async def get_settings_endpoint():
    """获取当前设置"""
    settings = get_settings()
    return JSONResponse(settings.model_dump())

@router.post("")
async def update_settings_endpoint(request: Request):
    """更新设置"""
    try:
        data = await request.json()
        settings = Settings(**data)
        save_settings(settings)
        return JSONResponse({"success": True, "settings": settings.model_dump()})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"设置更新失败: {str(e)}")

@router.get("/schema")
async def get_settings_schema():
    """获取设置Schema"""
    return JSONResponse({
        "llm": {
            "provider": {"type": "string", "enum": ["aliyun", "openai", "anthropic", "deepseek"]},
            "model": {"type": "string"},
            "base_url": {"type": "string"},
            "api_key": {"type": "string"},
            "max_tokens": {"type": "integer", "default": 4096},
            "temperature": {"type": "number", "default": 0.7}
        },
        "sandbox": {
            "enabled": {"type": "boolean", "default": True},
            "timeout": {"type": "integer", "default": 60}
        },
        "knowledge_base": {
            "enabled": {"type": "boolean", "default": True},
            "chunk_size": {"type": "integer", "default": 1000},
            "chunk_overlap": {"type": "integer", "default": 200}
        }
    })
