#!/usr/bin/env python3
"""
DATA-AI - 万能智能助手 (完整功能版本)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import sys
import json

# 添加项目路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 导入存储模块
from web.storage import initialize_storage, get_settings
from web.services import run_universal_agent

app = FastAPI(
    title="DATA-AI - 万能智能助手",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 挂载静态文件
static_path = BASE_DIR / "web" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 页面路由
@app.get("/", response_class=HTMLResponse)
async def get_index():
    html_file = BASE_DIR / "web" / "templates" / "doubao_index.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/agents", response_class=HTMLResponse)
async def get_agents():
    html_file = BASE_DIR / "web" / "templates" / "agents.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/prompts", response_class=HTMLResponse)
async def get_prompts():
    html_file = BASE_DIR / "web" / "templates" / "prompts.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/skills", response_class=HTMLResponse)
async def get_skills():
    html_file = BASE_DIR / "web" / "templates" / "skills.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/mcp", response_class=HTMLResponse)
async def get_mcp():
    html_file = BASE_DIR / "web" / "templates" / "mcp.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/settings", response_class=HTMLResponse)
async def get_settings_page():
    html_file = BASE_DIR / "web" / "templates" / "settings.html"
    with open(html_file, 'r', encoding='utf-8') as f:
        return f.read()

# WebSocket聊天
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "")
            
            # 发送思考状态
            await websocket.send_json({"type": "thinking", "content": "正在分析您的请求..."})
            
            try:
                settings = get_settings()
                
                # 使用完整的智能体处理
                await run_universal_agent(websocket, content, settings)
                
            except Exception as e:
                import traceback
                print(f"Agent error: {traceback.format_exc()}")
                await websocket.send_json({
                    "type": "response",
                    "content": f"已收到：{content}\n\n这是演示回复。"
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        pass

# 兼容旧版API调用
@app.post("/api/chat")
async def chat_endpoint(request: dict):
    content = request.get("content", "")
    return {
        "response": f"已收到：{content}\n\n请使用WebSocket进行聊天！",
        "success": True
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "5.0.0",
        "features": [
            "chat",
            "agents",
            "prompts",
            "skills",
            "mcp",
            "settings",
            "tidycup",
            "websocket"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # 初始化存储
    initialize_storage()
    
    print("🚀 DATA-AI 万能智能助手启动中...")
    print("📱 访问地址: http://localhost:8001")
    print("📚 API文档: http://localhost:8001/docs")
    print("="*50)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
