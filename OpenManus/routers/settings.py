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
from utils.validation import validate_schema_type
import json

router = APIRouter()


def _mask_settings(settings: Settings) -> dict:
    """对设置中的敏感信息进行脱敏"""
    data = settings.model_dump()
    if data.get("llm", {}).get("api_key"):
        key = data["llm"]["api_key"]
        if len(key) > 8:
            data["llm"]["api_key"] = key[:4] + "****" + key[-4:]
        else:
            data["llm"]["api_key"] = "****"
    if data.get("langsmith", {}).get("api_key"):
        key = data["langsmith"]["api_key"]
        if len(key) > 8:
            data["langsmith"]["api_key"] = key[:4] + "****" + key[-4:]
        else:
            data["langsmith"]["api_key"] = "****"
    return data


# ==================== 设置 CRUD ====================

@router.get("/api/settings")
async def get_settings():
    return JSONResponse(_mask_settings(database.current_settings))


@router.post("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    database.current_settings = Settings(**data)
    save_settings(database.current_settings)
    return JSONResponse({"success": True, "settings": database.current_settings.model_dump()})


# ==================== Schema ====================

@router.get("/api/schema/{schema_type}")
async def get_schema(schema_type: str):
    validate_schema_type(schema_type)
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

    # Provider-specific validation
    provider = llm.get("provider", "")

    # Common validations
    if not llm.get("api_key"):
        if provider != "ollama":  # Ollama doesn't need API key
            errors.append({"field": "llm.api_key", "message": "API Key 不能为空"})

    if llm.get("max_tokens"):
        max_tokens = llm["max_tokens"]
        if max_tokens < 1:
            errors.append({"field": "llm.max_tokens", "message": "max_tokens 必须大于 0"})

    if llm.get("temperature"):
        temp = llm["temperature"]
        if temp < 0 or temp > 2:
            errors.append({"field": "llm.temperature", "message": "temperature 应在 0-2 之间"})

    if llm.get("top_p"):
        top_p = llm["top_p"]
        if top_p < 0 or top_p > 1:
            errors.append({"field": "llm.top_p", "message": "top_p 应在 0-1 之间"})

    # Provider-specific validations
    if provider == "azure":
        if not llm.get("api_version"):
            errors.append({"field": "llm.api_version", "message": "Azure 需要指定 api_version"})
        if not llm.get("deployment_name"):
            errors.append({"field": "llm.deployment_name", "message": "Azure 需要指定 deployment_name"})

    if provider == "google":
        if llm.get("api_version") and not llm["api_version"]:
            errors.append({"field": "llm.api_version", "message": "Google 需要指定 api_version"})

    return JSONResponse({"valid": len(errors) == 0, "errors": errors})


@router.post("/api/settings/test-connection")
async def test_api_connection(request: Request):
    """测试 API 连接，提供详细的成功/失败反馈"""
    data = await request.json()
    llm = data.get("llm", {})
    api_key = llm.get("api_key", "")
    base_url = llm.get("base_url", "https://api.openai.com/v1")
    model = llm.get("model", "gpt-4o")
    provider = llm.get("provider", "openai")

    result = await test_connection(api_key, base_url, model, provider)
    return JSONResponse(result)


@router.post("/api/settings/verify-model")
async def verify_model(request: Request):
    """验证指定模型是否存在且可用"""
    data = await request.json()
    llm = data.get("llm", {})
    api_key = llm.get("api_key", "")
    base_url = llm.get("base_url", "https://api.openai.com/v1")
    model = llm.get("model", "")
    provider = llm.get("provider", "openai")

    if not model:
        return JSONResponse({
            "success": False,
            "message": "请指定要验证的模型名称",
            "error_type": "missing_model"
        })

    from services.llm_service import verify_model_exists
    result = await verify_model_exists(api_key, base_url, model, provider)
    return JSONResponse(result)


@router.post("/api/settings/list-models")
async def list_models(request: Request):
    """列出提供商所有可用的模型"""
    data = await request.json()
    llm = data.get("llm", {})
    api_key = llm.get("api_key", "")
    base_url = llm.get("base_url", "https://api.openai.com/v1")
    provider = llm.get("provider", "openai")

    from services.llm_service import list_available_models
    result = await list_available_models(api_key, base_url, provider)
    return JSONResponse(result)


@router.post("/api/settings/account-info")
async def get_account_info_endpoint(request: Request):
    """获取账户信息，包括购买渠道和余额"""
    data = await request.json()
    llm = data.get("llm", {})
    api_key = llm.get("api_key", "")
    base_url = llm.get("base_url", "https://api.openai.com/v1")
    provider = llm.get("provider", "openai")

    from services.llm_service import get_account_info
    result = await get_account_info(api_key, base_url, provider)
    return JSONResponse(result)


@router.get("/api/settings/export")
async def export_settings():
    return JSONResponse(_mask_settings(database.current_settings))


@router.post("/api/settings/import")
async def import_settings(request: Request):
    data = await request.json()
    try:
        database.current_settings = Settings(**data)
        save_settings(database.current_settings)
        return JSONResponse({"success": True, "message": "配置导入成功"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置格式错误: {str(e)}")


# ==================== Model Providers and Configurations ====================

@router.get("/api/settings/providers")
async def get_providers():
    """获取所有支持的模型提供商"""
    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "OpenAI 官方 API",
            "icon": "🤖",
            "default_base_url": "https://api.openai.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 4096, "min": 1, "max": 128000, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 2, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "top_k", "type": "number", "default": 0, "min": 0, "description": "Top-K采样"},
                {"name": "frequency_penalty", "type": "number", "default": 0, "min": -2, "max": 2, "description": "频率惩罚"},
                {"name": "presence_penalty", "type": "number", "default": 0, "min": -2, "max": 2, "description": "存在惩罚"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
                {"name": "n", "type": "number", "default": 1, "min": 1, "max": 128, "description": "返回数量"},
                {"name": "logprobs", "type": "number", "description": "对数概率"},
                {"name": "echo", "type": "boolean", "default": False, "description": "回显输入"},
                {"name": "best_of", "type": "number", "default": 1, "min": 1, "description": "最佳采样数"},
            ],
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16384},
                {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K", "context_window": 16384},
            ],
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "description": "Claude 系列模型",
            "icon": "🦜",
            "default_base_url": "https://api.anthropic.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 4096, "min": 1, "max": 409600, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "top_k", "type": "number", "default": 0, "min": 0, "description": "Top-K采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop_sequences", "type": "array", "description": "停止序列"},
                {"name": "anthropic_version", "type": "string", "default": "bedrock-2023-05-31", "description": "API版本"},
            ],
            "models": [
                {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context_window": 200000},
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
                {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_window": 200000},
                {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000},
            ],
        },
        {
            "id": "google",
            "name": "Google",
            "description": "Gemini 系列模型",
            "icon": "🔷",
            "default_base_url": "https://generativelanguage.googleapis.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_output_tokens", "type": "number", "default": 2048, "min": 1, "max": 8192, "description": "最大输出令牌"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.95, "min": 0, "max": 1, "description": "核采样"},
                {"name": "top_k", "type": "number", "default": 40, "min": 1, "max": 100, "description": "Top-K采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "api_version", "type": "string", "default": "v1", "description": "API版本"},
            ],
            "models": [
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context_window": 1000000},
                {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context_window": 1000000},
                {"id": "gemini-pro", "name": "Gemini Pro", "context_window": 32768},
                {"id": "gemini-pro-vision", "name": "Gemini Pro Vision", "context_window": 32768},
            ],
        },
        {
            "id": "azure",
            "name": "Azure OpenAI",
            "description": "Microsoft Azure OpenAI",
            "icon": "☁️",
            "default_base_url": "https://{resource}.openai.azure.com/",
            "requires_api_key": True,
            "required_fields": ["api_key", "model", "api_version", "deployment_name"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 4096, "min": 1, "max": 128000, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 2, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "frequency_penalty", "type": "number", "default": 0, "min": -2, "max": 2, "description": "频率惩罚"},
                {"name": "presence_penalty", "type": "number", "default": 0, "min": -2, "max": 2, "description": "存在惩罚"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
                {"name": "resource_name", "type": "string", "description": "Azure资源名称"},
            ],
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16384},
            ],
        },
        {
            "id": "ollama",
            "name": "Ollama",
            "description": "本地运行的开源模型",
            "icon": "🐑",
            "default_base_url": "http://localhost:11434/v1",
            "requires_api_key": False,
            "required_fields": ["model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 4096, "min": 1, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.8, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "num_ctx", "type": "number", "default": 8192, "min": 2048, "description": "上下文窗口"},
                {"name": "num_gpu", "type": "number", "default": 1, "description": "GPU数量"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "mirostat", "type": "number", "default": 0, "min": 0, "max": 2, "description": "Mirostat采样"},
                {"name": "mirostat_tau", "type": "number", "default": 5.0, "description": "Mirostat Tau"},
                {"name": "mirostat_eta", "type": "number", "default": 0.1, "description": "Mirostat Eta"},
                {"name": "repeat_last_n", "type": "number", "default": 64, "description": "重复惩罚范围"},
                {"name": "repeat_penalty", "type": "number", "default": 1.1, "description": "重复惩罚系数"},
                {"name": "tfs_z", "type": "number", "default": 1, "description": "Top-P典型采样"},
                {"name": "num_thread", "type": "number", "default": 0, "description": "线程数"},
            ],
            "models": [
                {"id": "llama3", "name": "LLaMA 3", "context_window": 8192},
                {"id": "llama3.1", "name": "LLaMA 3.1", "context_window": 128000},
                {"id": "mistral", "name": "Mistral", "context_window": 8192},
                {"id": "mixtral", "name": "Mixtral", "context_window": 32768},
                {"id": "phi3", "name": "Phi-3", "context_window": 8192},
                {"id": "qwen", "name": "Qwen", "context_window": 8192},
                {"id": "gemma", "name": "Gemma", "context_window": 8192},
                {"id": "zephyr", "name": "Zephyr", "context_window": 8192},
            ],
        },
        {
            "id": "aliyun",
            "name": "阿里云",
            "description": "通义千问系列模型",
            "icon": "⛅",
            "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 2048, "min": 1, "max": 16384, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 2, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "top_k", "type": "number", "default": 0, "min": 0, "description": "Top-K采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
                {"name": "seed", "type": "number", "description": "随机种子"},
                {"name": "enable_search", "type": "boolean", "default": False, "description": "启用搜索"},
                {"name": "api_type", "type": "string", "default": "dashscope", "description": "API类型"},
            ],
            "models": [
                {"id": "qwen-plus-latest", "name": "通义千问 Plus", "context_window": 128000},
                {"id": "qwen-turbo-latest", "name": "通义千问 Turbo", "context_window": 128000},
                {"id": "qwen-max", "name": "通义千问 Max", "context_window": 8192},
                {"id": "qwen-max-longcontext", "name": "通义千问 Max Long", "context_window": 128000},
                {"id": "qwen-7b-chat", "name": "通义千问 7B", "context_window": 8192},
            ],
        },
        {
            "id": "deepseek",
            "name": "深度求索",
            "description": "DeepSeek 系列模型",
            "icon": "🔍",
            "default_base_url": "https://api.deepseek.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 2048, "min": 1, "max": 8192, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "top_k", "type": "number", "default": 0, "min": 0, "description": "Top-K采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
            ],
            "models": [
                {"id": "deepseek-chat", "name": "DeepSeek Chat", "context_window": 8192},
                {"id": "deepseek-coder", "name": "DeepSeek Coder", "context_window": 16384},
                {"id": "deepseek-r1", "name": "DeepSeek R1", "context_window": 128000},
                {"id": "deepseek-r1-chat", "name": "DeepSeek R1 Chat", "context_window": 128000},
            ],
        },
        {
            "id": "doubao",
            "name": "豆包",
            "description": "字节跳动豆包模型",
            "icon": "🧇",
            "default_base_url": "https://api.doubao.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model", "secret_key"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 2048, "min": 1, "max": 4096, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
            ],
            "models": [
                {"id": "doubao-3.5s", "name": "豆包 3.5S", "context_window": 128000},
                {"id": "doubao-3.5", "name": "豆包 3.5", "context_window": 32768},
                {"id": "doubao-pro", "name": "豆包 Pro", "context_window": 8192},
            ],
        },
        {
            "id": "zhipu",
            "name": "智谱",
            "description": "智谱AI系列模型",
            "icon": "💎",
            "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 2048, "min": 1, "max": 8192, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "top_k", "type": "number", "default": 0, "min": 0, "description": "Top-K采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
                {"name": "repetition_penalty", "type": "number", "default": 1.0, "min": 1.0, "max": 2.0, "description": "重复惩罚"},
            ],
            "models": [
                {"id": "glm-4", "name": "GLM-4", "context_window": 128000},
                {"id": "glm-4-air", "name": "GLM-4 Air", "context_window": 8192},
                {"id": "glm-4-long", "name": "GLM-4 Long", "context_window": 200000},
                {"id": "glm-3-turbo", "name": "GLM-3 Turbo", "context_window": 8192},
            ],
        },
        {
            "id": "minimax",
            "name": "MiniMax",
            "description": "MiniMax 系列模型",
            "icon": "🔷",
            "default_base_url": "https://api.minimax.chat/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "optional_fields": [
                {"name": "max_tokens", "type": "number", "default": 2048, "min": 1, "max": 8192, "description": "最大令牌数"},
                {"name": "temperature", "type": "number", "default": 0.7, "min": 0, "max": 1, "description": "温度参数"},
                {"name": "top_p", "type": "number", "default": 0.9, "min": 0, "max": 1, "description": "核采样"},
                {"name": "stream", "type": "boolean", "default": False, "description": "流式输出"},
                {"name": "stop", "type": "array", "description": "停止词"},
                {"name": "reply_constraints", "type": "object", "description": "回复约束"},
            ],
            "models": [
                {"id": "abab6.5-chat", "name": "Abab6.5 Chat", "context_window": 128000},
                {"id": "abab6-chat", "name": "Abab6 Chat", "context_window": 8192},
                {"id": "abab5-chat", "name": "Abab5 Chat", "context_window": 4096},
            ],
        },
    ]
    return JSONResponse(providers)


@router.get("/api/settings/models")
async def get_available_models():
    """获取所有可用的模型列表（简化版，用于下拉选择）"""
    models = [
        # OpenAI
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "context_window": 128000},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "context_window": 128000},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai", "context_window": 128000},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai", "context_window": 16384},
        # Anthropic
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "context_window": 200000},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic", "context_window": 200000},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "provider": "anthropic", "context_window": 200000},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "provider": "anthropic", "context_window": 200000},
        # Google
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "context_window": 1000000},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google", "context_window": 1000000},
        {"id": "gemini-pro", "name": "Gemini Pro", "provider": "google", "context_window": 32768},
        # Azure
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "azure", "context_window": 128000},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "azure", "context_window": 128000},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "azure", "context_window": 16384},
        # Ollama
        {"id": "llama3", "name": "LLaMA 3", "provider": "ollama", "context_window": 8192},
        {"id": "llama3.1", "name": "LLaMA 3.1", "provider": "ollama", "context_window": 128000},
        {"id": "mistral", "name": "Mistral", "provider": "ollama", "context_window": 8192},
        {"id": "mixtral", "name": "Mixtral", "provider": "ollama", "context_window": 32768},
        {"id": "phi3", "name": "Phi-3", "provider": "ollama", "context_window": 8192},
        {"id": "qwen", "name": "Qwen", "provider": "ollama", "context_window": 8192},
        # Aliyun
        {"id": "qwen-plus-latest", "name": "通义千问 Plus", "provider": "aliyun", "context_window": 128000},
        {"id": "qwen-turbo-latest", "name": "通义千问 Turbo", "provider": "aliyun", "context_window": 128000},
        {"id": "qwen-max", "name": "通义千问 Max", "provider": "aliyun", "context_window": 8192},
        {"id": "qwen-max-longcontext", "name": "通义千问 Max Long", "provider": "aliyun", "context_window": 128000},
        # DeepSeek
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek", "context_window": 8192},
        {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "deepseek", "context_window": 16384},
        {"id": "deepseek-r1", "name": "DeepSeek R1", "provider": "deepseek", "context_window": 128000},
        {"id": "deepseek-r1-chat", "name": "DeepSeek R1 Chat", "provider": "deepseek", "context_window": 128000},
        # Doubao
        {"id": "doubao-3.5s", "name": "豆包 3.5S", "provider": "doubao", "context_window": 128000},
        {"id": "doubao-3.5", "name": "豆包 3.5", "provider": "doubao", "context_window": 32768},
        {"id": "doubao-pro", "name": "豆包 Pro", "provider": "doubao", "context_window": 8192},
        # Zhipu
        {"id": "glm-4", "name": "GLM-4", "provider": "zhipu", "context_window": 128000},
        {"id": "glm-4-air", "name": "GLM-4 Air", "provider": "zhipu", "context_window": 8192},
        {"id": "glm-4-long", "name": "GLM-4 Long", "provider": "zhipu", "context_window": 200000},
        {"id": "glm-3-turbo", "name": "GLM-3 Turbo", "provider": "zhipu", "context_window": 8192},
        # MiniMax
        {"id": "abab6.5-chat", "name": "Abab6.5 Chat", "provider": "minimax", "context_window": 128000},
        {"id": "abab6-chat", "name": "Abab6 Chat", "provider": "minimax", "context_window": 8192},
    ]
    return JSONResponse(models)
