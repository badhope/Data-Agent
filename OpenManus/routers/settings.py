"""
DataAgent - 设置路由
包含系统设置、验证、测试、导入导出、模型列表、Schema 等端点
连接测试委托给 services 层处理
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import database
from database import save_settings
from config import CONFIG_DIR
from models import Settings
from services.llm_service import test_connection
import json

router = APIRouter()


# ==================== 设置 CRUD ====================

@router.get("/api/settings")
async def get_settings():
    return JSONResponse(database.current_settings.model_dump())


@router.post("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    database.current_settings = Settings(**data)
    save_settings(database.current_settings)
    return JSONResponse({"success": True, "settings": database.current_settings.model_dump()})


# ==================== Schema ====================

@router.get("/api/schema/{schema_type}")
async def get_schema(schema_type: str):
    schema_file = CONFIG_DIR / "schema" / f"{schema_type}_schema.json"
    if not schema_file.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    with open(schema_file, 'r', encoding='utf-8') as f:
        return JSONResponse(json.load(f))


# ==================== 设置验证/测试/导入导出/模型列表 ====================

@router.post("/api/settings/validate")
async def validate_settings(request: Request):
    data = await request.json()
    errors = []
    llm = data.get("llm", {})
    if not llm.get("api_key"):
        errors.append({"field": "llm.api_key", "message": "API Key 不能为空"})
    if llm.get("max_tokens") and (llm["max_tokens"] < 1 or llm["max_tokens"] > 128000):
        errors.append({"field": "llm.max_tokens", "message": "max_tokens 应在 1-128000 之间"})
    if llm.get("temperature") and (llm["temperature"] < 0 or llm["temperature"] > 2):
        errors.append({"field": "llm.temperature", "message": "temperature 应在 0-2 之间"})
    return JSONResponse({"valid": len(errors) == 0, "errors": errors})


@router.post("/api/settings/test-connection")
async def test_api_connection(request: Request):
    """测试 API 连接，委托给 services 层"""
    data = await request.json()
    llm = data.get("llm", {})
    api_key = llm.get("api_key", "")
    base_url = llm.get("base_url", "https://api.openai.com/v1")
    model = llm.get("model", "gpt-4o")
    result = await test_connection(api_key, base_url, model)
    return JSONResponse(result)


@router.get("/api/settings/export")
async def export_settings():
    return JSONResponse(database.current_settings.model_dump())


@router.post("/api/settings/import")
async def import_settings(request: Request):
    data = await request.json()
    try:
        database.current_settings = Settings(**data)
        save_settings(database.current_settings)
        return JSONResponse({"success": True, "message": "配置导入成功"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置格式错误: {str(e)}")


@router.get("/api/settings/models")
async def get_available_models():
    models = [
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google"},
        {"id": "qwen-plus-latest", "name": "通义千问 Plus", "provider": "aliyun"},
        {"id": "qwen-turbo-latest", "name": "通义千问 Turbo", "provider": "aliyun"},
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek"},
        {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "deepseek"},
    ]
    return JSONResponse(models)
