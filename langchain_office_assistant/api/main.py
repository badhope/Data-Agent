from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents import (
    create_office_agent,
    run_office_assistant,
    TraceRecorder,
)
from utils.config import config

app = FastAPI(title="Office Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class TraceRequest(BaseModel):
    trace_id: str

class TraceResponse(BaseModel):
    trace_id: str
    content: str

class SessionRequest(BaseModel):
    session_id: str

class ToolListResponse(BaseModel):
    tools: List[Dict[str, str]]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await run_office_assistant(
            user_input=request.message,
            session_id=request.session_id,
            config={
                "agent_model": config.agent_model,
                "openai_api_key": config.openai_api_key,
                "redis_url": config.redis_url,
            }
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/{session_id}")
async def get_session_history(session_id: str):
    try:
        from agents import MemoryManager
        memory_manager = MemoryManager(config.redis_url)
        history = memory_manager.get_chat_history(session_id)
        messages = history.messages
        return {"session_id": session_id, "messages": [{"type": m.type, "content": m.content} for m in messages]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{session_id}")
async def delete_session(session_id: str):
    try:
        from agents import MemoryManager
        memory_manager = MemoryManager(config.redis_url)
        memory_manager.delete_session(session_id)
        return {"status": "success", "message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trace/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: str):
    try:
        trace_recorder = TraceRecorder()
        content = trace_recorder.visualize_trace(trace_id)
        return TraceResponse(trace_id=trace_id, content=content)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/traces/{session_id}")
async def get_session_traces(session_id: str):
    try:
        trace_recorder = TraceRecorder()
        traces = trace_recorder.get_traces_by_session(session_id)
        return {
            "session_id": session_id,
            "traces": [{"trace_id": t.trace_id, "created_at": t.created_at, "user_input": t.user_input} for t in traces]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools", response_model=ToolListResponse)
async def get_tools():
    try:
        agent = create_office_agent()
        tools = agent.get_available_tools()
        return ToolListResponse(tools=tools)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "office-agent-api"}

def run_api(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_api()