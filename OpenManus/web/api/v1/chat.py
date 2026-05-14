"""
Chat API Router
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio
import json
from pathlib import Path

from web.core.dependencies import get_current_user
from web.services import run_universal_agent, call_llm
from web.storage import get_settings, save_message

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception:
                self.disconnect(user_id)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                
                # 发送思考中状态
                await manager.send_personal_message({
                    "type": "thinking",
                    "title": "正在分析",
                    "content": "理解您的请求..."
                }, user_id)
                
                # 处理消息
                result = await process_chat_message(message_data)
                
                # 发送结果
                await manager.send_personal_message(result, user_id)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "content": "消息格式错误"
                }, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "content": f"服务器错误: {str(e)}"
        }, user_id)
        manager.disconnect(user_id)

async def process_chat_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理聊天消息"""
    content = message_data.get("content", "")
    options = message_data.get("options", {})
    
    try:
        settings = get_settings()
        
        # 使用智能体处理
        result = await run_universal_agent(content, settings)
        
        return {
            "type": "response",
            "content": result.get("output", "处理完成"),
            "metadata": result.get("metadata", {})
        }
        
    except Exception as e:
        return {
            "type": "error",
            "content": f"处理失败: {str(e)}"
        }

@router.post("/send")
async def send_message_endpoint(request: Dict[str, Any]):
    """发送聊天消息（非WebSocket方式）"""
    try:
        result = await process_chat_message(request)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
