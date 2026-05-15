"""
DataAgent - 万能智能助手
模块化 Web 应用入口
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import HTMLResponse

# 导入润色处理函数
from services.polish_service import handle_polish_request

# 初始化数据库
from database import init_all
init_all()

# 创建 FastAPI 应用
app = FastAPI(title="DataAgent", description="万能智能助手")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 鲁棒性中间件
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.rate_limiter import RateLimitMiddleware

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

# WebSocket 端点 - 必须在其他路由之前定义
from services.agent_service import run_universal_agent
from services.input_sanitizer import validate_message
from services.intent_router import route_intent

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "message")
            message = data.get("content", "")
            options = data.get("options", {})
            files = data.get("files", [])
            client_settings = data.get("settings", {})

            # 构建配置对象
            settings = {
                "llm": {
                    "provider": client_settings.get("provider", "aliyun"),
                    "api_key": client_settings.get("apiKey", client_settings.get("api_key", "sk-eae25c29cf9c4607b7241c979e15876d")),
                    "base_url": client_settings.get("apiUrl", client_settings.get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
                    "model": client_settings.get("model", "qwen-plus-latest"),
                    "temperature": client_settings.get("temperature", 0.7),
                    "max_tokens": client_settings.get("maxTokens", client_settings.get("max_tokens", 8192)),
                    "top_p": 0.9
                },
                "sandbox": {
                    "enabled": True,
                    "timeout": 60
                }
            }

            # 处理润色请求
            if message_type == "polish":
                text = data.get("content", "")
                style = data.get("style", "academic")
                await handle_polish_request(text, style, websocket, settings)
                continue

            # 输入验证
            validation = validate_message(message)
            if not validation["valid"]:
                await websocket.send_json({"type": "error", "content": validation["error"]})
                continue

            # 使用净化后的输入
            if validation.get("sanitized") != message:
                message = validation["sanitized"]
                if validation.get("warning"):
                    await websocket.send_json({
                        "type": "thinking",
                        "title": "⚠️ 安全提示",
                        "content": validation["warning"]
                    })

            # 意图识别：检查是否匹配特定功能
            intent_result = await route_intent(message, files, websocket, settings)
            if intent_result:
                # 已由意图路由处理，跳过通用Agent
                continue

            # 通用Agent处理
            await run_universal_agent(websocket, message, settings=settings, options=options)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# 注册路由
from routers.settings import router as settings_router
from routers.knowledge import router as knowledge_router
from routers.skills import router as skills_router
from routers.mcp import router as mcp_router
from routers.conversations import router as conversations_router
from routers.databases import router as databases_router
from routers.financial import router as financial_router
from routers.nl2sql import router as nl2sql_router
from routers.visualization import router as visualization_router
from routers.agent import router as agent_router
from routers.feedback import router as feedback_router
from routers.documents import router as documents_router
from routers.logs import router as logs_router

app.include_router(settings_router)
app.include_router(knowledge_router)
app.include_router(skills_router)
app.include_router(mcp_router)
app.include_router(conversations_router)
app.include_router(databases_router)
app.include_router(financial_router)
app.include_router(nl2sql_router)
app.include_router(visualization_router)
app.include_router(agent_router)
app.include_router(feedback_router)
app.include_router(documents_router)
app.include_router(logs_router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "DataAgent"}

@app.post("/api/test-connection")
async def test_connection(request: dict):
    """测试LLM连接"""
    from openai import AsyncOpenAI
    try:
        client = AsyncOpenAI(
            api_key=request.get("apiKey", request.get("api_key", "")),
            base_url=request.get("apiUrl", request.get("api_url", ""))
        )
        await client.chat.completions.create(
            model=request.get("model", "qwen-plus-latest"),
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/install-package")
async def install_package(request: dict):
    """安装Python包"""
    import subprocess
    package = request.get("package", "")
    if not package:
        return {"success": False, "error": "请提供包名"}

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return {"success": True, "message": f"{package} 安装成功"}
        else:
            return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "安装超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 首页路由 - 聊天界面
@app.get("/")
async def get():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 日志查看器页面路由
@app.get("/logs")
async def logs():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "logs.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 管理界面路由 - 智能体、技能、工具
@app.get("/agents")
async def agents():
    html_path = os.path.join(os.path.dirname(__file__), "web", "templates", "agents.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/skills")
async def skills():
    html_path = os.path.join(os.path.dirname(__file__), "web", "templates", "skills.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/mcp")
async def mcp():
    html_path = os.path.join(os.path.dirname(__file__), "web", "templates", "mcp.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="DataAgent Web Interface")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    logger.info("Starting DataAgent Web Interface...")
    uvicorn.run(app, host=args.host, port=args.port)
