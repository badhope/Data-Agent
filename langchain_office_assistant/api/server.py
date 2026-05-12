from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import time
import uuid
import os
import sys
import json
import httpx
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="Office Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
traces = []
system_config = {
    "platform": "dashscope",
    "model": "qwen-plus",
    "api_key": "",
    "temperature": 0.7,
    "max_tokens": 2000,
}

TOOLS = [
    {"id": "calculator", "name": "计算工具", "desc": "数学计算和货币换算", "icon": "🧮", "color": "blue"},
    {"id": "calendar", "name": "日程管理", "desc": "查看和安排日程", "icon": "📅", "color": "green"},
    {"id": "task", "name": "任务管理", "desc": "创建和跟踪任务", "icon": "✅", "color": "purple"},
    {"id": "email", "name": "邮件处理", "desc": "发送和搜索邮件", "icon": "📧", "color": "orange"},
    {"id": "document", "name": "文档处理", "desc": "阅读和摘要文档", "icon": "📄", "color": "red"},
    {"id": "chart", "name": "图表生成", "desc": "生成各种图表", "icon": "📊", "color": "blue"},
    {"id": "ppt", "name": "PPT生成", "desc": "创建演示文稿", "icon": "📽️", "color": "green"},
    {"id": "knowledge", "name": "知识库", "desc": "智能问答", "icon": "📚", "color": "purple"},
]

plugin_settings = {tool["id"]: {"enabled": True} for tool in TOOLS}

SYSTEM_PROMPT = """你是一个专业的办公智能体，具备多种办公能力：

可用工具：
- 🧮 计算工具：数学计算、统计分析、货币换算、单位转换
- 📅 日程管理：查看日程、创建会议、设置提醒
- ✅ 任务管理：创建任务、更新状态、设置优先级
- 📧 邮件管理：发送邮件、搜索邮件、阅读邮件
- 📄 文档处理：读取文档、写入文档、智能摘要
- 📊 图表生成：生成折线图、柱状图、饼图、雷达图等
- 📽️ PPT生成：创建演示文稿、添加幻灯片
- 📚 知识库：向量检索、文档问答

回复规则：
- 使用友好、专业的中文语言
- 对于复杂查询，提供详细的步骤说明
- 如果需要调用工具，说明调用了什么工具
- 直接回答用户的问题，不要重复用户的问题
"""

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    trace_id: str
    intent: str
    confidence: float
    tool_used: Optional[str]
    duration_ms: int

class ToolListResponse(BaseModel):
    tools: List[Dict[str, str]]

class ConfigRequest(BaseModel):
    platform: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class PluginSettingsRequest(BaseModel):
    plugin_id: str
    enabled: bool

def get_intent(message: str) -> tuple:
    msg = message.lower()
    if any(word in msg for word in ["计算", "加", "减", "乘", "除", "等于", "多少", "calc"]):
        return ("calculator", 0.9)
    elif any(word in msg for word in ["日程", "会议", "时间", "calendar", "schedule"]):
        return ("calendar", 0.85)
    elif any(word in msg for word in ["任务", "todo", "task", "完成", "待办"]):
        return ("task", 0.8)
    elif any(word in msg for word in ["邮件", "email", "写信"]):
        return ("email", 0.75)
    elif any(word in msg for word in ["文档", "document", "read", "文件"]):
        return ("document", 0.7)
    elif any(word in msg for word in ["图表", "chart", "图", "统计"]):
        return ("chart", 0.75)
    elif any(word in msg for word in ["ppt", "演示", "slide", "幻灯片"]):
        return ("ppt", 0.7)
    elif any(word in msg for word in ["知识库", "搜索", "knowledge", "查询", "查找"]):
        return ("knowledge", 0.8)
    else:
        return ("chat", 0.6)

async def call_dashscope_api(messages: list) -> str:
    api_key = system_config.get("api_key", "")
    if not api_key:
        return "❌ API Key 未配置，请在设置页面配置API Key后再试。"
    
    model = system_config.get("model", "qwen-plus")
    temperature = system_config.get("temperature", 0.7)
    max_tokens = system_config.get("max_tokens", 2000)
    
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                return f"❌ API调用失败 (HTTP {response.status_code}): {error_msg}"
    except httpx.TimeoutException:
        return "❌ API请求超时，请稍后重试。"
    except httpx.ConnectError:
        return "❌ 无法连接到API服务器，请检查网络连接。"
    except Exception as e:
        return f"❌ API调用异常: {str(e)}"

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        start_time = time.time()
        
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
        if request.session_id not in sessions:
            sessions[request.session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        intent, confidence = get_intent(request.message)
        
        if intent != "chat" and not plugin_settings.get(intent, {}).get("enabled", True):
            response = f"抱歉，{intent} 插件当前已禁用。您可以在设置中启用此功能。"
            tool_used = None
        elif system_config.get("api_key"):
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            for msg in sessions[request.session_id]["messages"][-10:]:
                api_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            api_messages.append({"role": "user", "content": request.message})
            
            response = await call_dashscope_api(api_messages)
            tool_used = intent if intent != "chat" else None
        else:
            response = generate_mock_response(request.message, intent)
            tool_used = intent if intent != "chat" else None
        
        trace_id = str(uuid.uuid4())
        trace = {
            "trace_id": trace_id,
            "session_id": request.session_id,
            "user_input": request.message,
            "created_at": datetime.now().isoformat(),
            "intent": intent
        }
        traces.append(trace)
        
        sessions[request.session_id]["messages"].append({
            "role": "user",
            "content": request.message
        })
        sessions[request.session_id]["messages"].append({
            "role": "assistant",
            "content": response
        })
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            trace_id=trace_id,
            intent=intent,
            confidence=confidence,
            tool_used=tool_used,
            duration_ms=duration_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_mock_response(message: str, intent: str) -> str:
    return f"⚠️ API Key 未配置，当前为演示模式。\n\n您发送的消息：{message}\n识别意图：{intent}\n\n请在「API 配置」页面配置 API Key 后使用完整功能。"

@app.get("/chat/{session_id}")
async def get_session_history(session_id: str):
    try:
        if session_id not in sessions:
            return {"session_id": session_id, "messages": []}
        return {"session_id": session_id, "messages": sessions[session_id]["messages"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{session_id}")
async def delete_session(session_id: str):
    try:
        if session_id in sessions:
            del sessions[session_id]
        return {"status": "success", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    try:
        session_list = []
        for sid, data in sessions.items():
            msg_count = len(data["messages"]) // 2
            last_msg = data["messages"][-1]["content"][:50] + "..." if data["messages"] else ""
            session_list.append({
                "session_id": sid,
                "created_at": data["created_at"],
                "message_count": msg_count,
                "last_message": last_msg
            })
        return {"sessions": session_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    try:
        trace = next((t for t in traces if t["trace_id"] == trace_id), None)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        return {"trace_id": trace_id, "content": f"Trace details: {trace}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/traces/{session_id}")
async def get_session_traces(session_id: str):
    try:
        session_traces = [t for t in traces if t["session_id"] == session_id]
        return {"session_id": session_id, "traces": session_traces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools", response_model=ToolListResponse)
async def get_tools():
    try:
        tools_with_status = []
        for tool in TOOLS:
            tool_data = tool.copy()
            tool_data["enabled"] = plugin_settings.get(tool["id"], {}).get("enabled", True)
            tools_with_status.append(tool_data)
        return ToolListResponse(tools=tools_with_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    safe_config = system_config.copy()
    if safe_config.get("api_key"):
        safe_config["api_key"] = safe_config["api_key"][:8] + "****" + safe_config["api_key"][-4:]
    return {"config": safe_config}

@app.post("/config")
async def update_config(config_req: ConfigRequest):
    try:
        if config_req.platform is not None:
            system_config["platform"] = config_req.platform
        if config_req.model is not None:
            system_config["model"] = config_req.model
        if config_req.api_key is not None:
            system_config["api_key"] = config_req.api_key
        if config_req.temperature is not None:
            system_config["temperature"] = config_req.temperature
        if config_req.max_tokens is not None:
            system_config["max_tokens"] = config_req.max_tokens
        
        safe_config = system_config.copy()
        if safe_config.get("api_key"):
            safe_config["api_key"] = safe_config["api_key"][:8] + "****" + safe_config["api_key"][-4:]
        return {"status": "success", "message": "Config updated", "config": safe_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plugins/settings")
async def update_plugin_settings(settings_req: PluginSettingsRequest):
    try:
        if settings_req.plugin_id not in plugin_settings:
            plugin_settings[settings_req.plugin_id] = {}
        plugin_settings[settings_req.plugin_id]["enabled"] = settings_req.enabled
        return {
            "status": "success",
            "message": "Plugin settings updated",
            "plugin_id": settings_req.plugin_id,
            "enabled": settings_req.enabled
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "office-agent-api",
        "sessions": len(sessions),
        "traces": len(traces),
        "plugins": len(TOOLS),
        "api_configured": bool(system_config.get("api_key"))
    }

@app.get("/stats")
async def get_stats():
    try:
        total_messages = sum(len(s["messages"]) for s in sessions.values())
        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "total_traces": len(traces),
            "active_plugins": sum(1 for s in plugin_settings.values() if s.get("enabled", True))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
