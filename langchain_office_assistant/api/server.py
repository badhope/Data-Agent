from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import time
import uuid
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="Office Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
sessions = {}
traces = []
system_config = {
    "platform": "dashscope",
    "model": "qwen-plus",
    "api_key": "",
    "temperature": 0.7,
    "max_tokens": 2000,
}

# Tool definitions
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

# Plugin settings
plugin_settings = {
    tool["id"]: {"enabled": True} for tool in TOOLS
}

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

def calculate_response(expression: str) -> str:
    """模拟计算功能"""
    try:
        if "加" in expression or "+" in expression:
            parts = expression.replace("加", "+").split("+")
            result = sum(float(p.strip()) for p in parts if p.strip())
            return f"计算结果：{result}"
        elif "减" in expression or "-" in expression:
            parts = expression.split("减") if "减" in expression else expression.split("-")
            if len(parts) >= 2:
                result = float(parts[0].strip()) - sum(float(p.strip()) for p in parts[1:])
                return f"计算结果：{result}"
        elif "乘" in expression or "*" in expression or "x" in expression:
            return "乘法运算完成（演示）"
        elif "除" in expression or "/" in expression:
            return "除法运算完成（演示）"
        else:
            return f"已收到计算请求：{expression}（演示模式）"
    except:
        return f"计算请求已收到：{expression}（演示模式）"

def generate_response(message: str, intent: str) -> str:
    responses = {
        "calculator": f"好的，让我为您计算一下：{message}\n\n{calculate_response(message)}\n\n💡 提示：这是演示版本，完整功能需要配置真实API。",
        "calendar": f"📅 日程请求已收到：{message}\n\n📌 已为您安排日程（演示模式）\n\n💡 提示：完整功能支持与日历API集成。",
        "task": f"✅ 任务管理请求：{message}\n\n📝 任务已记录到您的待办列表（演示模式）\n\n💡 提示：完整功能支持任务优先级、提醒、进度跟踪。",
        "email": f"📧 邮件处理请求：{message}\n\n✉️ 邮件已准备发送（演示模式）\n\n💡 提示：完整功能支持邮件模板、批量发送、附件管理。",
        "document": f"📄 文档处理请求：{message}\n\n📖 文档已分析完成（演示模式）\n\n💡 提示：完整功能支持Word/Excel/PDF处理、OCR识别。",
        "chart": f"📊 图表生成请求：{message}\n\n📈 图表已生成（演示模式）\n\n💡 提示：完整功能支持10+图表类型、数据导入、样式定制。",
        "ppt": f"📽️ PPT生成请求：{message}\n\n🎯 演示文稿已创建（演示模式）\n\n💡 提示：完整功能支持模板、智能排版、动画效果。",
        "knowledge": f"📚 知识库查询：{message}\n\n🔍 正在检索相关文档...（演示模式）\n\n💡 提示：完整功能支持向量检索、语义搜索、多文档问答。",
        "chat": f"您好！我收到了您的消息：{message}\n\n🤖 我是Office Agent，我可以帮助您：\n- 🧮 数学计算、单位换算\n- 📅 日程管理、会议安排\n- ✅ 任务跟踪、待办管理\n- 📧 邮件处理、自动回复\n- 📄 文档处理、智能摘要\n- 📊 图表生成、数据分析\n- 📽️ PPT自动生成\n- 📚 知识库问答\n\n有什么我可以帮您的吗？"
    }
    return responses.get(intent, responses["chat"])

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        start_time = time.time()
        
        # Get or create session
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
        if request.session_id not in sessions:
            sessions[request.session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        # Get intent
        intent, confidence = get_intent(request.message)
        
        # Check if plugin is enabled
        if intent != "chat" and not plugin_settings.get(intent, {}).get("enabled", True):
            response = f"抱歉，{intent} 插件当前已禁用。您可以在设置中启用此功能。"
            tool_used = None
        else:
            # Generate response
            response = generate_response(request.message, intent)
            tool_used = intent if intent != "chat" else None
        
        # Store trace
        trace_id = str(uuid.uuid4())
        trace = {
            "trace_id": trace_id,
            "session_id": request.session_id,
            "user_input": request.message,
            "created_at": datetime.now().isoformat(),
            "intent": intent
        }
        traces.append(trace)
        
        # Update session
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
        return {
            "trace_id": trace_id,
            "content": f"Trace details for {trace_id}: {trace}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/traces/{session_id}")
async def get_session_traces(session_id: str):
    try:
        session_traces = [t for t in traces if t["session_id"] == session_id]
        return {
            "session_id": session_id,
            "traces": session_traces
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools", response_model=ToolListResponse)
async def get_tools():
    try:
        # Combine TOOLS with enabled status
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
    try:
        return {
            "config": system_config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        return {
            "status": "success",
            "message": "Config updated",
            "config": system_config
        }
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
        "plugins": len(TOOLS)
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
