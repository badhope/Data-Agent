from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import time
import uuid
import os
from datetime import datetime

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

# Mock tools
TOOLS = [
    {"id": "calculator", "name": "计算工具", "desc": "数学计算和货币换算"},
    {"id": "calendar", "name": "日程管理", "desc": "查看和安排日程"},
    {"id": "task", "name": "任务管理", "desc": "创建和跟踪任务"},
    {"id": "email", "name": "邮件处理", "desc": "发送和搜索邮件"},
    {"id": "document", "name": "文档处理", "desc": "阅读和摘要文档"},
    {"id": "chart", "name": "图表生成", "desc": "生成各种图表"},
    {"id": "ppt", "name": "PPT生成", "desc": "创建演示文稿"},
    {"id": "knowledge", "name": "知识库", "desc": "智能问答"},
]

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

def get_intent(message: str) -> tuple:
    msg = message.lower()
    if any(word in msg for word in ["计算", "加", "减", "乘", "除", "等于", "多少", "calc"]):
        return ("calculator", 0.9)
    elif any(word in msg for word in ["日程", "会议", "时间", "calendar"]):
        return ("calendar", 0.85)
    elif any(word in msg for word in ["任务", "todo", "task", "完成"]):
        return ("task", 0.8)
    elif any(word in msg for word in ["邮件", "email"]):
        return ("email", 0.75)
    elif any(word in msg for word in ["文档", "document", "read"]):
        return ("document", 0.7)
    elif any(word in msg for word in ["图表", "chart", "图"]):
        return ("chart", 0.75)
    elif any(word in msg for word in ["ppt", "演示", "slide"]):
        return ("ppt", 0.7)
    elif any(word in msg for word in ["知识库", "搜索", "knowledge", "查询"]):
        return ("knowledge", 0.8)
    else:
        return ("chat", 0.6)

def generate_response(message: str, intent: str):
    responses = {
        "calculator": f"好的，让我为您计算一下：{message}\n\n这是计算的结果。(模拟)",
        "calendar": f"日程请求已收到：{message}\n\n这是日程管理的结果。(模拟)",
        "task": f"任务管理请求：{message}\n\n任务已记录。(模拟)",
        "email": f"邮件处理请求：{message}\n\n邮件已处理。(模拟)",
        "document": f"文档处理请求：{message}\n\n文档已分析。(模拟)",
        "chart": f"图表生成请求：{message}\n\n图表已生成。(模拟)",
        "ppt": f"PPT生成请求：{message}\n\nPPT已创建。(模拟)",
        "knowledge": f"知识库查询：{message}\n\n这是查询结果。(模拟)",
        "chat": f"您好！我收到了您的消息：{message}\n\n有什么我可以帮助您的吗？"
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
        
        # Generate response
        response = generate_response(request.message, intent)
        
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
            tool_used=intent if intent != "chat" else None,
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
        return ToolListResponse(tools=TOOLS)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "office-agent-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
