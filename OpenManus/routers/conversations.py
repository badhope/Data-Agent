"""
DataAgent - 对话路由
包含对话 CRUD、搜索、导出、分享等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import conversations, save_conversations
from config import DATA_DIR
from utils.validation import validate_share_id
import json, uuid, datetime, re
from pathlib import Path

router = APIRouter()


# ==================== 对话 CRUD ====================

@router.get("/api/conversations")
async def list_conversations():
    return JSONResponse(list(conversations.values()))


@router.post("/api/conversations")
async def create_conversation(request: Request):
    data = await request.json()
    conv_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    conversation = {
        "id": conv_id,
        "title": data.get("title", "新对话"),
        "messages": [],
        "created_at": now,
        "updated_at": now
    }
    conversations[conv_id] = conversation
    save_conversations()
    return JSONResponse(conversation)


@router.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    return JSONResponse(conversations[conv_id])


@router.put("/api/conversations/{conv_id}")
async def update_conversation(conv_id: str, request: Request):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    data = await request.json()
    conversations[conv_id]["title"] = data.get("title", conversations[conv_id]["title"])
    conversations[conv_id]["messages"] = data.get("messages", conversations[conv_id]["messages"])
    conversations[conv_id]["updated_at"] = datetime.datetime.now().isoformat()
    save_conversations()
    return JSONResponse(conversations[conv_id])


@router.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    del conversations[conv_id]
    save_conversations()
    return JSONResponse({"success": True, "message": "对话已删除"})


# ==================== 对话搜索 ====================

@router.get("/api/conversations/search")
async def search_conversations(q: str = ""):
    if not q:
        return JSONResponse([])
    results = []
    for conv_id, conv in conversations.items():
        title_match = q.lower() in conv.get("title", "").lower()
        content_match = False
        for msg in conv.get("messages", []):
            if q.lower() in msg.get("content", "").lower():
                content_match = True
                break
        if title_match or content_match:
            results.append({
                "id": conv_id,
                "title": conv.get("title", ""),
                "updated_at": conv.get("updated_at", ""),
                "match_type": "title" if title_match else "content"
            })
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    return JSONResponse(results)


# ==================== 对话导出 ====================

@router.get("/api/conversations/{conv_id}/export")
async def export_conversation(conv_id: str, format: str = "json"):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    conv = conversations[conv_id]
    if format == "markdown" or format == "md":
        lines = [f"# {conv.get('title', '对话记录')}\n"]
        lines.append(f"导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        lines.append("---\n\n")
        for msg in conv.get("messages", []):
            role = "用户" if msg.get("type") == "user" else "助手" if msg.get("type") == "assistant" else "系统"
            lines.append(f"**{role}**:\n\n{msg.get('content', '')}\n\n")
        content = "\n".join(lines)
        return JSONResponse({"format": "markdown", "content": content})
    else:
        return JSONResponse({"format": "json", "content": conv})


# ==================== 对话分享 ====================

@router.post("/api/conversations/{conv_id}/share")
async def share_conversation(conv_id: str):
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    conv = conversations[conv_id]
    share_id = str(uuid.uuid4())[:8]
    if not re.match(r'^[a-zA-Z0-9]+$', share_id):
        raise HTTPException(status_code=400, detail="无效的分享ID")
    share_file = DATA_DIR / "shares" / f"{share_id}.json"
    share_file.parent.mkdir(parents=True, exist_ok=True)
    with open(share_file, 'w', encoding='utf-8') as f:
        json.dump({
            "id": share_id,
            "conversation": conv,
            "created_at": datetime.datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    return JSONResponse({"share_id": share_id, "share_url": f"/api/conversations/shared/{share_id}"})


@router.get("/api/conversations/shared/{share_id}")
async def get_shared_conversation(share_id: str):
    validate_share_id(share_id)
    share_file = DATA_DIR / "shares" / f"{share_id}.json"
    if not share_file.exists():
        raise HTTPException(status_code=404, detail="分享链接不存在或已过期")
    with open(share_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return JSONResponse(data)
