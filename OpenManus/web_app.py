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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("content", "")

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

            await run_universal_agent(websocket, message)
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

# 首页路由 - 聊天界面
@app.get("/")
async def get():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 功能入口页面路由
@app.get("/features")
async def features():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "features.html")
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
    logger.info("Starting DataAgent Web Interface...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
