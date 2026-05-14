"""
DATA-AI Main Application
Architecture inspired by Dify and other GitHub open-source projects
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import json

# 确保能找到模块
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from web.api import api_router
from web.core.config import get_settings

app_settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="DATA-AI - 万能智能助手",
    description="完整的智能助手系统：知识库、技能系统、MCP工具、数据清洗",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = BASE_DIR / "web" / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket disconnected: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Send error: {e}")
                self.disconnect(user_id)

manager = ConnectionManager()

@app.websocket("/api/v1/chat/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for chat"""
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                content = message_data.get("content", "")
                
                # 发送思考中
                await manager.send_personal_message({
                    "type": "thinking",
                    "title": "处理中",
                    "content": "正在理解您的需求..."
                }, user_id)
                
                # 模拟处理
                import asyncio
                await asyncio.sleep(0.5)
                
                # 发送回复
                response = {
                    "type": "response",
                    "content": f"收到您的消息：{content}\n\n这是一个模拟回复。系统已完整重构为模块化架构，支持：\n\n- API版本化\n- WebSocket实时通信\n- 知识库管理\n- 技能系统\n- MCP工具\n- 财务分析（海峡杯/泰迪杯功能）"
                }
                
                await manager.send_personal_message(response, user_id)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "content": "消息格式错误"
                }, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(user_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "app": "DATA-AI - 万能智能助手"
    }

@app.get("/")
async def root():
    """Root endpoint - serve HTML"""
    template_path = BASE_DIR / "web" / "templates" / "index.html"
    if template_path.exists():
        return FileResponse(str(template_path))
    return {"message": "DATA-AI API Server"}

@app.get("/api/v1/status")
async def system_status():
    """Get system status"""
    return {
        "status": "online",
        "version": "2.0.0",
        "features": [
            "knowledge_base",
            "skill_system",
            "mcp_tools",
            "analytics",
            "websocket"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting DATA-AI Server...")
    print(f"📦 Version: 2.0.0")
    print(f"📍 Directory: {BASE_DIR}")
    print("="*50)
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
