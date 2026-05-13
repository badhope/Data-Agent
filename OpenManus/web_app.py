"""
DataAgent - 万能智能助手
模块化 Web 应用入口
"""
import sys
import os

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 鲁棒性中间件
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.rate_limiter import RateLimitMiddleware

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

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

# WebSocket 端点
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
        print(f"WebSocket error: {e}")

# 首页路由
@app.get("/")
async def get():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting DataAgent Web Interface...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
