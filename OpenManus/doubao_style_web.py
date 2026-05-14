#!/usr/bin/env python3
"""
DATA-AI - 万能智能助手 (豆包风格 + Trae IDE 风格管理界面)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio

app = FastAPI(
    title="DATA-AI - 万能智能助手",
    version="4.0.0"
)

BASE_DIR = Path(__file__).parent

# 挂载静态文件
static_path = BASE_DIR / "web" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.0.0", "style": "豆包风格 + Trae IDE 管理界面"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "")
            await websocket.send_json({"type": "thinking", "content": "正在思考..."})
            await asyncio.sleep(1)
            reply = f"已收到：{content}\n\n这是模拟回复，实际功能开发中..."
            await websocket.send_json({"type": "response", "content": reply})
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    print("🚀 DATA-AI 豆包风格界面启动中...")
    print("📱 访问地址: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
