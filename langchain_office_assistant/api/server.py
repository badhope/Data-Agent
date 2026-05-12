from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="Office Agent API", version="1.0.0")

from api.sandbox_routes import router as sandbox_router
app.include_router(sandbox_router)

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
    "model": "qwen-flash",
    "api_key": "sk-a9aa5c63a3384a75a2e54c89240ef02a",
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
    {"id": "sandbox", "name": "代码沙箱", "desc": "运行Python/JavaScript代码", "icon": "💻", "color": "cyan"},
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
- 💻 代码沙箱：运行Python/JavaScript代码，生成图表和数据可视化

回复规则：
- 使用友好、专业的中文语言
- 对于复杂查询，提供详细的步骤说明
- 如果需要调用工具，说明调用了什么工具
- 直接回答用户的问题，不要重复用户的问题
"""

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class DeleteMessageRequest(BaseModel):
    session_id: str
    message_index: int

class ChatResponse(BaseModel):
    response: str
    session_id: str
    trace_id: str
    intent: str
    confidence: float
    tool_used: Optional[str]
    duration_ms: int
    thinking: Optional[List[Dict[str, Any]]] = None

class ToolListResponse(BaseModel):
    tools: List[Dict[str, Any]]

class ConfigRequest(BaseModel):
    platform: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class PluginSettingsRequest(BaseModel):
    plugin_id: str
    enabled: bool

INTENT_KEYWORDS = {
    "calculator": ["计算", "加", "减", "乘", "除", "等于", "多少", "calc", "换算", "转换", "统计"],
    "calendar": ["日程", "会议", "时间安排", "calendar", "schedule", "提醒", "预约"],
    "task": ["任务", "todo", "task", "完成", "待办", "进度", "跟踪"],
    "email": ["邮件", "email", "写信", "发送邮件", "收件", "回复"],
    "document": ["文档", "document", "read", "文件", "摘要", "阅读", "总结"],
    "chart": ["图表", "chart", "柱状图", "折线图", "饼图", "雷达图", "散点图", "可视化"],
    "ppt": ["ppt", "演示", "slide", "幻灯片", "汇报", "展示"],
    "knowledge": ["知识库", "搜索", "knowledge", "查询", "查找", "检索", "问答"],
    "sandbox": ["运行代码", "执行代码", "写代码", "代码", "编程", "python", "javascript", "code", "跑一下", "运行脚本", "写个程序", "编程实现"],
}

def get_intent_keyword(message: str) -> tuple:
    msg = message.lower()
    best_intent = "chat"
    best_confidence = 0.6
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in msg:
                conf = min(0.95, 0.7 + len(kw) * 0.03)
                if conf > best_confidence:
                    best_intent = intent
                    best_confidence = conf
                break
    return (best_intent, best_confidence)

async def get_intent_ai(message: str) -> tuple:
    if not system_config.get("api_key"):
        return get_intent_keyword(message)
    try:
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {"Authorization": f"Bearer {system_config['api_key']}", "Content-Type": "application/json"}
        payload = {
            "model": system_config.get("model", "qwen-flash"),
            "messages": [
                {"role": "system", "content": """你是意图识别专家。分析用户输入，返回JSON格式的意图识别结果。

可用意图类型：calculator, calendar, task, email, document, chart, ppt, knowledge, chat

规则：
- calculator: 数学计算、单位换算、统计分析
- calendar: 日程安排、会议、提醒
- task: 任务管理、待办事项
- email: 邮件相关
- document: 文档处理、摘要
- chart: 图表生成、数据可视化
- ppt: PPT/演示文稿
- knowledge: 知识库检索、搜索查询
- chat: 普通闲聊、问候、其他

只输出JSON，不要其他文字：
{"intent":"xxx","confidence":0.95}"""},
                {"role": "user", "content": message}
            ],
            "temperature": 0,
            "max_tokens": 100
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                import re
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    data = json.loads(json_match.group())
                    intent = data.get("intent", "chat")
                    confidence = data.get("confidence", 0.8)
                    if intent in INTENT_KEYWORDS or intent == "chat":
                        return (intent, confidence)
            return get_intent_keyword(message)
    except Exception:
        return get_intent_keyword(message)

def get_intent(message: str) -> tuple:
    return get_intent_keyword(message)

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
                error_data = {}
                try:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                except:
                    pass
                
                error_msg = error_data.get("error", {}).get("message", error_data.get("message", ""))
                error_code = error_data.get("error", {}).get("code", error_data.get("code", ""))
                
                if response.status_code == 401:
                    return f"❌ 【API认证失败】(HTTP 401)\n\n原因：API Key无效或已过期\n\n解决方案：\n1. 请检查「API 配置」页面中的API Key是否正确\n2. 如果API Key已过期，请到阿里云百炼平台重新获取\n3. 确保API Key格式正确（以sk-开头）"
                elif response.status_code == 403:
                    return f"❌ 【API访问被拒绝】(HTTP 403)\n\n原因：没有权限访问该资源，可能是：\n1. API Key没有开通对应服务\n2. 账户余额不足或额度用完\n3. 请求频率超出限制\n\n错误详情：{error_msg or '无'}\n\n解决方案：\n1. 登录阿里云百炼平台检查账户余额和额度\n2. 确认已开通 qwen-flash 模型服务\n3. 等待一段时间后重试（如果是频率限制）"
                elif response.status_code == 429:
                    return f"❌ 【API请求过于频繁】(HTTP 429)\n\n原因：请求频率超出API限制\n\n解决方案：\n1. 降低请求频率\n2. 等待几秒后再重试\n3. 考虑升级API套餐以获得更高配额"
                elif response.status_code >= 500:
                    return f"❌ 【API服务器内部错误】(HTTP {response.status_code})\n\n原因：阿里云百炼服务器暂时不可用\n\n错误详情：{error_msg or response.text[:200]}\n\n解决方案：\n1. 这是服务端问题，请稍后重试\n2. 可以访问阿里云状态页面查看服务状态"
                else:
                    return f"❌ 【API调用失败】(HTTP {response.status_code})\n\n错误代码：{error_code or '无'}\n错误详情：{error_msg or response.text[:500]}\n\n请检查API请求参数是否正确，或联系阿里云技术支持。"
    except httpx.TimeoutException:
        return f"❌ 【请求超时】\n\n原因：API请求在60秒内未收到响应\n\n可能原因：\n1. 网络连接不稳定\n2. 服务器响应缓慢\n3. 请求内容过长\n\n解决方案：\n1. 检查网络连接\n2. 尝试简化问题或减少上下文\n3. 稍后重试"
    except httpx.ConnectError as e:
        return f"❌ 【网络连接失败】\n\n原因：无法连接到阿里云API服务器\n\n错误详情：{str(e)}\n\n可能原因：\n1. 网络被防火墙阻止\n2. DNS解析失败\n3. 网络代理配置问题\n\n解决方案：\n1. 检查网络连接\n2. 检查防火墙和代理设置\n3. 尝试使用VPN"
    except httpx.RequestError as e:
        return f"❌ 【网络请求错误】\n\n错误类型：{type(e).__name__}\n错误详情：{str(e)}\n\n解决方案：\n1. 检查网络连接\n2. 稍后重试"
    except Exception as e:
        return f"❌ 【API调用异常】\n\n错误类型：{type(e).__name__}\n错误详情：{str(e)}\n\n这是一个意外错误，请记录错误信息并联系开发者。"

def generate_thinking_chain(user_message: str, intent: str, confidence: float) -> List[Dict[str, Any]]:
    """生成思维链"""
    chain = []
    
    # 步骤1：理解用户问题
    chain.append({
        "title": "理解用户问题",
        "content": f"分析用户输入：「{user_message}」"
    })
    
    # 步骤2：识别意图
    intent_names = {
        "calculator": "计算工具",
        "calendar": "日程管理",
        "task": "任务管理",
        "email": "邮件处理",
        "document": "文档处理",
        "chart": "图表生成",
        "ppt": "PPT生成",
        "knowledge": "知识库",
        "chat": "普通对话"
    }
    chain.append({
        "title": "识别用户意图",
        "content": f"识别为「{intent_names.get(intent, intent)}」，置信度 {int(confidence * 100)}%"
    })
    
    # 步骤3：根据意图思考下一步
    if intent == "calculator":
        chain.append({
            "title": "思考计算方法",
            "content": "识别到计算意图，准备进行数学运算"
        })
    elif intent == "chart":
        chain.append({
            "title": "思考图表生成",
            "content": "识别到图表意图，准备生成可视化图表"
        })
    elif intent == "chat":
        chain.append({
            "title": "规划回复策略",
            "content": "识别到普通对话，准备友好回复用户"
        })
    elif intent == "sandbox":
        chain.append({
            "title": "思考代码执行",
            "content": "识别到代码执行意图，准备在沙箱环境中运行代码"
        })
    
    # 步骤4：生成回复
    chain.append({
        "title": "生成最终回复",
        "content": "整合思考，生成最终回复内容"
    })
    
    return chain

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
        
        intent, confidence = await get_intent_ai(request.message)
        
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
        
        # 生成思维链
        thinking = generate_thinking_chain(request.message, intent, confidence)
        
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
            duration_ms=duration_ms,
            thinking=thinking
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

@app.delete("/chat/{session_id}/message/{message_index}")
async def delete_message(session_id: str, message_index: int):
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        msgs = sessions[session_id]["messages"]
        if message_index < 0 or message_index >= len(msgs):
            raise HTTPException(status_code=400, detail="Invalid message index")
        deleted = msgs.pop(message_index)
        return {
            "status": "success",
            "message": "Message deleted",
            "deleted_role": deleted["role"],
            "remaining_messages": len(msgs)
        }
    except HTTPException:
        raise
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

if FRONTEND_DIR.exists():
    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/frontend/{file_path:path}")
    async def serve_frontend_file(file_path: str):
        file = FRONTEND_DIR / file_path
        if file.exists() and file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
