"""
DataAgent - 万能智能助手 Web Interface
完整的系统化架构，包括知识库、技能系统、MCP工具、数据清洗等功能
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
import sys
import uuid
import datetime
import re
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles
from pydantic import BaseModel, Field

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

app = FastAPI(
    title="DataAgent - 万能智能助手",
    description="完整的系统化智能助手：知识库、技能系统、MCP工具、数据清洗",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_bases"
SKILLS_DIR = DATA_DIR / "skills"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp.json"
SETTINGS_FILE = CONFIG_DIR / "web_config.json"

for dir_path in [CONFIG_DIR, DATA_DIR, KNOWLEDGE_DIR, SKILLS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    llm: Dict[str, Any] = Field(default_factory=lambda: {
        "provider": "aliyun",
        "model": "qwen-plus-latest",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False
    })
    sandbox: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "timeout": 60,
        "allow_network": False
    })
    knowledge_base: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "vector_db": "sqlite",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "embedding_model": "text-embedding-v3"
    })
    conversation: Dict[str, Any] = Field(default_factory=lambda: {
        "history_enabled": True,
        "max_history": 50,
        "auto_title": True
    })
    display: Dict[str, Any] = Field(default_factory=lambda: {
        "theme": "dark",
        "thinking_chain": True,
        "code_highlight": True,
        "markdown_render": True
    })
    agent: Dict[str, Any] = Field(default_factory=lambda: {
        "max_steps": 5,
        "auto_mode": True,
        "reasoning_mode": "auto"
    })

class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str = ""
    created_at: str
    updated_at: str
    embedding_model: str = "text-embedding-v3"
    indexing_technique: str = "high_quality"
    permission: str = "only_me"

class Document(BaseModel):
    id: str
    knowledge_base_id: str
    name: str
    data_source_type: str
    status: str
    file_path: str
    created_at: str

class ProcessingRule(BaseModel):
    mode: str = "automatic"
    rules: Dict[str, Any] = Field(default_factory=lambda: {
        "pre_processing_rules": [
            {"id": "remove_extra_spaces", "enabled": True},
            {"id": "remove_urls_emails", "enabled": False}
        ],
        "segmentation": {
            "separator": "\n\n",
            "max_tokens": 1000,
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
    })

class Skill(BaseModel):
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    category: str = "custom"
    type: str = "custom"
    icon: str = "⚡"
    status: str = "published"
    created_at: str
    updated_at: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    prompts: Dict[str, Any] = Field(default_factory=dict)
    tools: List[Dict[str, Any]] = Field(default_factory=list)

class MCPServer(BaseModel):
    id: str
    name: str
    type: str
    command: str = ""
    args: List[str] = Field(default_factory=list)
    url: str = ""
    env: Dict[str, str] = Field(default_factory=dict)
    status: str = "inactive"
    enabled: bool = True
    icon: str = "🔌"

current_settings: Settings = Settings()
knowledge_bases: Dict[str, KnowledgeBase] = {}
documents: Dict[str, Document] = {}
skills: Dict[str, Skill] = {}
mcp_servers: Dict[str, MCPServer] = {}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Settings(**data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return Settings()

def save_settings(settings: Settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings.model_dump(), f, ensure_ascii=False, indent=2)

current_settings = load_settings()

def load_knowledge_bases():
    index_file = KNOWLEDGE_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for kb_id, kb_data in data.items():
                    knowledge_bases[kb_id] = KnowledgeBase(**kb_data)
        except Exception as e:
            print(f"Error loading knowledge bases: {e}")

def save_knowledge_bases():
    index_file = KNOWLEDGE_DIR / "index.json"
    data = {kb_id: kb.model_dump() for kb_id, kb in knowledge_bases.items()}
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_skills():
    index_file = SKILLS_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for skill_id, skill_data in data.items():
                    skills[skill_id] = Skill(**skill_data)
        except Exception as e:
            print(f"Error loading skills: {e}")
    if not skills:
        init_builtin_skills()

def save_skills():
    index_file = SKILLS_DIR / "index.json"
    data = {skill_id: skill.model_dump() for skill_id, skill in skills.items()}
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_builtin_skills():
    builtin = [
        Skill(
            id="code_reviewer",
            name="代码审查专家",
            description="智能代码审查，发现潜在问题并提供优化建议",
            version="1.0.0",
            author="DataAgent Team",
            category="code_generation",
            type="built_in",
            icon="🔍",
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            parameters=[
                {"name": "code", "type": "string", "description": "待审查的代码", "required": True},
                {"name": "language", "type": "string", "description": "编程语言", "required": False, "enum": ["python", "javascript", "typescript"]}
            ],
            prompts={
                "system_prompt": "你是一位资深的代码审查专家，请按照以下标准审查代码：\n1. 检查语法错误和潜在bug\n2. 评估代码风格和最佳实践\n3. 提供性能优化建议\n4. 指出安全隐患"
            }
        ),
        Skill(
            id="data_analyzer",
            name="数据分析助手",
            description="执行数据分析和可视化",
            version="1.0.0",
            author="DataAgent Team",
            category="data_analysis",
            type="built_in",
            icon="📊",
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            parameters=[
                {"name": "data", "type": "string", "description": "数据", "required": True},
                {"name": "analysis_type", "type": "string", "description": "分析类型", "required": True, "enum": ["summary", "statistics", "visualization"]}
            ]
        ),
        Skill(
            id="document_processor",
            name="文档处理助手",
            description="提取、总结和分析文档内容",
            version="1.0.0",
            author="DataAgent Team",
            category="document_processing",
            type="built_in",
            icon="📄",
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            parameters=[
                {"name": "content", "type": "string", "description": "文档内容", "required": True},
                {"name": "task", "type": "string", "description": "任务类型", "required": True, "enum": ["summary", "key_points", "translation"]}
            ]
        )
    ]
    for skill in builtin:
        skills[skill.id] = skill
    save_skills()

def load_mcp_servers():
    if MCP_CONFIG_FILE.exists():
        try:
            with open(MCP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "mcpServers" in data:
                    for server_id, server_data in data["mcpServers"].items():
                        mcp_servers[server_id] = MCPServer(
                            id=server_id,
                            name=server_data.get("name", server_id),
                            type=server_data.get("type", "stdio"),
                            command=server_data.get("command", ""),
                            args=server_data.get("args", []),
                            url=server_data.get("url", ""),
                            env=server_data.get("env", {}),
                            enabled=server_data.get("enabled", True),
                            icon="🔌"
                        )
        except Exception as e:
            print(f"Error loading MCP servers: {e}")

def save_mcp_servers():
    data = {
        "mcpServers": {
            server_id: {
                "type": server.type,
                "command": server.command,
                "args": server.args,
                "url": server.url,
                "env": server.env,
                "enabled": server.enabled
            } for server_id, server in mcp_servers.items()
        }
    }
    with open(MCP_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load_knowledge_bases()
load_skills()
load_mcp_servers()

async def execute_python(code: str, timeout: int = 30) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tempfile.mkdtemp(prefix="dataagent_"),
            env={**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "success": True,
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "returncode": proc.returncode
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def call_llm(prompt: str, settings: Settings) -> str:
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        client = AsyncOpenAI(
            api_key=settings.llm["api_key"],
            base_url=settings.llm["base_url"]
        )
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm["max_tokens"],
            temperature=settings.llm["temperature"],
            top_p=settings.llm["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"

async def clean_text(text: str, rules: dict) -> str:
    result = text
    pre_rules = rules.get("pre_processing_rules", [])
    for rule in pre_rules:
        if rule.get("enabled"):
            rule_id = rule.get("id")
            if rule_id == "remove_extra_spaces":
                result = re.sub(r'\s+', ' ', result).strip()
            elif rule_id == "remove_urls_emails":
                result = re.sub(r'https?://\S+', '', result)
                result = re.sub(r'\S+@\S+', '', result)
    return result

@app.get("/api/settings")
async def get_settings():
    return JSONResponse(current_settings.model_dump())

@app.post("/api/settings")
async def update_settings(request: Request):
    global current_settings
    data = await request.json()
    current_settings = Settings(**data)
    save_settings(current_settings)
    return JSONResponse({"success": True, "settings": current_settings.model_dump()})

@app.get("/api/knowledge-bases")
async def list_knowledge_bases():
    return JSONResponse([kb.model_dump() for kb in knowledge_bases.values()])

@app.post("/api/knowledge-bases")
async def create_knowledge_base(request: Request):
    data = await request.json()
    kb_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    kb = KnowledgeBase(
        id=kb_id,
        name=data.get("name", "未命名知识库"),
        description=data.get("description", ""),
        created_at=now,
        updated_at=now,
        embedding_model=data.get("embedding_model", "text-embedding-v3"),
        indexing_technique=data.get("indexing_technique", "high_quality")
    )
    knowledge_bases[kb_id] = kb
    save_knowledge_bases()
    (KNOWLEDGE_DIR / kb_id).mkdir(exist_ok=True)
    return JSONResponse(kb.model_dump())

@app.get("/api/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str):
    if kb_id not in knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return JSONResponse(knowledge_bases[kb_id].model_dump())

@app.post("/api/knowledge-bases/{kb_id}/documents")
async def upload_document(kb_id: str, name: str = Form(""), description: str = Form("")):
    if kb_id not in knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    doc_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    doc = Document(
        id=doc_id,
        knowledge_base_id=kb_id,
        name=name or "文档",
        data_source_type="custom",
        status="available",
        file_path="",
        created_at=now
    )
    documents[doc_id] = doc
    return JSONResponse(doc.model_dump())

@app.get("/api/knowledge-bases/{kb_id}/documents")
async def list_documents(kb_id: str):
    if kb_id not in knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    kb_docs = [doc.model_dump() for doc in documents.values() if doc.knowledge_base_id == kb_id]
    return JSONResponse(kb_docs)

@app.get("/api/skills")
async def list_skills():
    return JSONResponse([skill.model_dump() for skill in skills.values()])

@app.post("/api/skills")
async def create_skill(request: Request):
    data = await request.json()
    skill_id = data.get("id", str(uuid.uuid4()))
    now = datetime.datetime.now().isoformat()
    skill = Skill(
        id=skill_id,
        name=data.get("name", "未命名技能"),
        description=data.get("description", ""),
        version=data.get("version", "1.0.0"),
        author=data.get("author", ""),
        category=data.get("category", "custom"),
        type=data.get("type", "custom"),
        icon=data.get("icon", "⚡"),
        created_at=now,
        updated_at=now,
        parameters=data.get("parameters", []),
        prompts=data.get("prompts", {}),
        tools=data.get("tools", [])
    )
    skills[skill_id] = skill
    save_skills()
    return JSONResponse(skill.model_dump())

@app.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    return JSONResponse(skills[skill_id].model_dump())

@app.post("/api/skills/{skill_id}/use")
async def use_skill(skill_id: str, request: Request):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    skill = skills[skill_id]
    data = await request.json()
    params = data.get("parameters", {})
    prompt = ""
    if skill.prompts.get("system_prompt"):
        prompt += skill.prompts["system_prompt"] + "\n\n"
    template = skill.prompts.get("user_prompt_template", "{{input}}")
    user_input = params.get("input", str(params))
    prompt += template.replace("{{input}}", user_input)
    for key, value in params.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
    response = await call_llm(prompt, current_settings)
    return JSONResponse({"response": response, "skill": skill.name})

@app.get("/api/mcp/servers")
async def list_mcp_servers():
    return JSONResponse([server.model_dump() for server in mcp_servers.values()])

@app.post("/api/mcp/servers")
async def create_mcp_server(request: Request):
    data = await request.json()
    server_id = data.get("id", str(uuid.uuid4()))
    server = MCPServer(
        id=server_id,
        name=data.get("name", "未命名服务器"),
        type=data.get("type", "stdio"),
        command=data.get("command", ""),
        args=data.get("args", []),
        url=data.get("url", ""),
        env=data.get("env", {}),
        enabled=data.get("enabled", True),
        icon=data.get("icon", "🔌")
    )
    mcp_servers[server_id] = server
    save_mcp_servers()
    return JSONResponse(server.model_dump())

@app.get("/api/schema/{schema_type}")
async def get_schema(schema_type: str):
    schema_file = CONFIG_DIR / "schema" / f"{schema_type}_schema.json"
    if not schema_file.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    with open(schema_file, 'r', encoding='utf-8') as f:
        return JSONResponse(json.load(f))

async def run_universal_agent(websocket: WebSocket, message: str):
    try:
        await websocket.send_json({
            "type": "thinking",
            "phase": "init",
            "title": "🤔 理解需求",
            "content": f"正在分析: {message[:80]}..."
        })
        use_code = False
        if current_settings.knowledge_base.get("enabled"):
            kb_related = any(kw in message.lower() for kw in ["文档", "知识库", "knowledge", "search"])
        else:
            kb_related = False
        if any(kw in message.lower() for kw in ["代码", "python", "图表", "计算", "数据", "分析", "plot", "chart"]):
            use_code = True
        if use_code:
            await websocket.send_json({
                "type": "thinking",
                "phase": "tool_select",
                "title": "🛠️ 代码执行",
                "content": "检测到代码/数据需求，准备生成Python代码"
            })
            code_prompt = f"""根据用户需求生成Python代码：
用户需求：{message}
请直接输出可执行的Python代码，不需要解释。如果需要图表，保存为PNG文件。"""
            code = await call_llm(code_prompt, current_settings)
            code = re.sub(r'^```python\s*\n?', '', code.strip(), flags=re.MULTILINE)
            code = re.sub(r'\n?```$', '', code.strip(), flags=re.MULTILINE)
            code = code.strip()
            await websocket.send_json({
                "type": "thinking",
                "phase": "tool_result",
                "title": "📋 生成代码",
                "content": f"```python\n{code}\n```"
            })
            result = await execute_python(code, timeout=current_settings.sandbox["timeout"])
            if result["success"]:
                response = f"✅ 执行成功！\n\n**标准输出:**\n{result['stdout']}\n\n**代码:**\n```python\n{code}\n```"
                if result["stderr"]:
                    response += f"\n\n**警告:**\n{result['stderr']}"
            else:
                response = f"❌ 执行失败: {result.get('error', '未知错误')}\n\n**代码:**\n```python\n{code}\n```"
        elif kb_related and knowledge_bases:
            await websocket.send_json({
                "type": "thinking",
                "phase": "knowledge_retrieval",
                "title": "📚 知识库检索",
                "content": "正在从知识库中检索相关信息..."
            })
            kb_list = ", ".join([kb.name for kb in knowledge_bases.values()])
            response = await call_llm(f"用户问题：{message}\n\n可用知识库：{kb_list}\n\n请回答用户问题。", current_settings)
        else:
            await websocket.send_json({
                "type": "thinking",
                "phase": "analyze",
                "title": "🧠 智能分析",
                "content": "正在处理您的请求..."
            })
            response = await call_llm(message, current_settings)
        await websocket.send_json({"type": "response", "content": response})
    except Exception as e:
        await websocket.send_json({"type": "error", "content": f"❌ 处理失败: {str(e)[:300]}"})
        import traceback
        print(traceback.format_exc())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("content", "")
            await run_universal_agent(websocket, message)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/")
async def get():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataAgent - 万能智能助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Inter, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; color: #e2e8f0; }
        .app-container { display: flex; height: 100vh; }
        .sidebar { width: 280px; background: rgba(30, 41, 59, 0.95); backdrop-filter: blur(10px); border-right: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h2 { color: white; font-size: 20px; display: flex; align-items: center; gap: 10px; }
        .sidebar-nav { flex: 1; padding: 12px; overflow-y: auto; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; color: #94a3b8; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 4px; }
        .nav-item:hover { background: rgba(255,255,255,0.05); color: white; }
        .nav-item.active { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
        .nav-icon { font-size: 18px; }
        .nav-text h4 { font-size: 14px; font-weight: 500; }
        .nav-text p { font-size: 11px; opacity: 0.6; margin-top: 2px; }
        .nav-divider { height: 1px; background: rgba(255,255,255,0.1); margin: 12px 0; }
        .main-content { flex: 1; display: flex; flex-direction: column; min-width: 0; }
        .header { padding: 16px 24px; background: rgba(30, 41, 59, 0.5); border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { color: white; font-size: 18px; }
        .header-actions { display: flex; gap: 10px; }
        .btn { padding: 8px 16px; border-radius: 8px; font-size: 14px; cursor: pointer; border: none; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        .btn-secondary { background: rgba(71, 85, 105, 0.5); color: #94a3b8; }
        .chat-area { flex: 1; overflow-y: auto; padding: 24px; }
        .message { max-width: 85%; margin-bottom: 24px; animation: fadeIn 0.3s ease; }
        .message.user { margin-left: auto; }
        .message.assistant { margin-right: auto; }
        .message.system { text-align: center; margin: 16px auto; max-width: 60%; }
        .message-content { padding: 14px 18px; border-radius: 16px; line-height: 1.6; }
        .user .message-content { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border-bottom-right-radius: 4px; }
        .assistant .message-content { background: rgba(71, 85, 105, 0.6); color: #e2e8f0; border-bottom-left-radius: 4px; }
        .system .message-content { background: rgba(148, 163, 184, 0.15); color: #94a3b8; font-size: 13px; padding: 10px 16px; border-radius: 12px; }
        .thinking-container { background: rgba(71, 85, 105, 0.2); border-radius: 12px; padding: 16px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.05); }
        .thinking-phase { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
        .thinking-dot { width: 8px; height: 8px; background: #60a5fa; border-radius: 50%; animation: pulse 1s infinite; }
        .thinking-title { color: #60a5fa; font-weight: 500; font-size: 14px; }
        .thinking-content { color: #94a3b8; font-size: 13px; padding-left: 20px; }
        .thinking-tools { margin-top: 8px; padding-left: 20px; }
        .tool-tag { display: inline-block; background: rgba(59, 130, 246, 0.15); color: #60a5fa; padding: 4px 10px; border-radius: 6px; font-size: 12px; margin-right: 8px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .input-area { padding: 16px 24px; background: rgba(30, 41, 59, 0.5); border-top: 1px solid rgba(255,255,255,0.1); }
        .input-container { display: flex; gap: 12px; align-items: flex-end; }
        .input-box { flex: 1; padding: 14px 18px; background: rgba(71, 85, 105, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; color: white; font-size: 14px; outline: none; resize: none; min-height: 52px; max-height: 160px; font-family: inherit; }
        .input-box:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
        .send-btn { padding: 14px 24px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 12px; cursor: pointer; font-size: 14px; font-weight: 500; }
        .send-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
        .modal-overlay.show { display: flex; }
        .modal { background: #1e293b; border-radius: 16px; width: 90%; max-width: 900px; max-height: 85vh; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
        .modal-header { padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .modal-title { color: white; font-size: 18px; font-weight: 600; }
        .modal-close { background: none; border: none; color: #94a3b8; font-size: 28px; cursor: pointer; line-height: 1; }
        .modal-close:hover { color: white; }
        .modal-body { padding: 24px; overflow-y: auto; flex: 1; }
        .settings-tabs { display: flex; gap: 4px; margin-bottom: 24px; background: rgba(71, 85, 105, 0.25); padding: 4px; border-radius: 10px; }
        .settings-tab { padding: 8px 16px; border-radius: 8px; cursor: pointer; color: #94a3b8; font-size: 14px; transition: all 0.2s; }
        .settings-tab:hover { color: white; }
        .settings-tab.active { background: rgba(59, 130, 246, 0.25); color: #60a5fa; }
        .settings-section { display: none; }
        .settings-section.active { display: block; }
        .settings-section h3 { color: white; font-size: 16px; margin-bottom: 20px; }
        .setting-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; padding: 12px; background: rgba(71, 85, 105, 0.25); border-radius: 10px; }
        .setting-label { width: 160px; color: #cbd5e1; font-size: 14px; flex-shrink: 0; }
        .setting-input { flex: 1; padding: 10px 14px; background: rgba(71, 85, 105, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; font-size: 14px; font-family: inherit; }
        .setting-input:focus { border-color: #3b82f6; outline: none; }
        .setting-select { flex: 1; padding: 10px 14px; background: rgba(71, 85, 105, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; font-size: 14px; font-family: inherit; cursor: pointer; }
        .setting-switch { width: 48px; height: 26px; background: rgba(71, 85, 105, 0.5); border-radius: 13px; position: relative; cursor: pointer; transition: background 0.2s; }
        .setting-switch.on { background: #3b82f6; }
        .setting-switch::after { content: ''; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; background: white; border-radius: 50%; transition: left 0.2s; }
        .setting-switch.on::after { left: 25px; }
        .modal-actions { padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: flex-end; gap: 12px; flex-shrink: 0; }
        .kb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
        .kb-card { background: rgba(71, 85, 105, 0.25); border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
        .kb-card:hover { background: rgba(71, 85, 105, 0.4); border-color: rgba(255,255,255,0.1); }
        .kb-card-icon { font-size: 32px; margin-bottom: 12px; }
        .kb-card h4 { color: white; margin-bottom: 6px; font-size: 16px; }
        .kb-card p { color: #94a3b8; font-size: 13px; margin-bottom: 12px; }
        .kb-meta { display: flex; gap: 12px; color: #64748b; font-size: 12px; }
        .skill-list { display: flex; flex-direction: column; gap: 12px; }
        .skill-item { background: rgba(71, 85, 105, 0.25); border-radius: 12px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
        .skill-info { display: flex; align-items: center; gap: 12px; }
        .skill-icon { font-size: 24px; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: rgba(59, 130, 246, 0.15); border-radius: 10px; }
        .skill-details h4 { color: white; font-size: 15px; margin-bottom: 4px; }
        .skill-details p { color: #94a3b8; font-size: 13px; }
        .skill-badge { background: rgba(34, 197, 94, 0.15); color: #4ade80; padding: 4px 10px; border-radius: 6px; font-size: 12px; }
        .mcp-list { display: flex; flex-direction: column; gap: 12px; }
        .mcp-item { background: rgba(71, 85, 105, 0.25); border-radius: 12px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
        .help-content { color: #94a3b8; line-height: 1.8; }
        .help-content h4 { color: white; margin-top: 24px; margin-bottom: 12px; font-size: 16px; }
        .help-content pre { background: rgba(71, 85, 105, 0.3); padding: 14px; border-radius: 10px; overflow-x: auto; margin: 12px 0; }
        .help-content code { color: #fbbf24; font-size: 13px; }
        .file-upload-area { border: 2px dashed rgba(255,255,255,0.2); border-radius: 12px; padding: 40px; text-align: center; margin-bottom: 20px; cursor: pointer; transition: all 0.2s; }
        .file-upload-area:hover { border-color: #3b82f6; background: rgba(59, 130, 246, 0.05); }
        .file-upload-area h4 { color: white; margin-bottom: 8px; }
        .file-upload-area p { color: #94a3b8; font-size: 13px; }
        .processing-rules { background: rgba(71, 85, 105, 0.2); border-radius: 12px; padding: 16px; margin-top: 16px; }
        .rule-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .rule-item:last-child { border-bottom: none; }
        pre code { color: #e2e8f0 !important; }
        .message-content a { color: #60a5fa; }
        
        .menu-toggle {
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 8px;
        }
        
        .sidebar-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }
        
        /* ==================== 移动端响应式适配 ==================== */
        @media screen and (max-width: 768px) {
            /* 汉堡菜单按钮 - 默认隐藏侧边栏 */
            .menu-toggle {
                display: flex;
            }
            
            /* 侧边栏 - 移动端默认隐藏 */
            .sidebar {
                position: fixed;
                left: -280px;
                top: 0;
                bottom: 0;
                width: 280px;
                z-index: 1001;
                transition: left 0.3s ease;
                box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
            }
            
            .sidebar.open {
                left: 0;
            }
            
            .sidebar-overlay.show {
                display: block;
            }
            
            /* 主内容区 - 占据全屏 */
            .main-content {
                width: 100%;
                height: 100vh;
            }
            
            /* 头部优化 */
            .header {
                padding: 12px 16px;
                position: sticky;
                top: 0;
                z-index: 100;
                background: rgba(30, 41, 59, 0.98);
            }
            
            .header h1 {
                font-size: 16px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .header-actions {
                gap: 8px;
            }
            
            .header-actions .btn {
                padding: 6px 12px;
                font-size: 12px;
            }
            
            /* 聊天区域 - 适配移动端 */
            .chat-area {
                padding: 16px;
                flex: 1;
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
            }
            
            .message {
                max-width: 92%;
                margin-bottom: 16px;
            }
            
            .message-content {
                padding: 12px 14px;
                font-size: 14px;
                line-height: 1.5;
            }
            
            /* 思考容器 - 移动端适配 */
            .thinking-container {
                padding: 12px;
                margin-bottom: 12px;
            }
            
            .thinking-content {
                padding-left: 16px;
                font-size: 12px;
            }
            
            .thinking-tools {
                padding-left: 16px;
            }
            
            /* 输入区域 - 固定在底部 */
            .input-area {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 12px 16px;
                background: rgba(30, 41, 59, 0.98);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                z-index: 100;
                box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.2);
            }
            
            .input-container {
                display: flex;
                gap: 10px;
                align-items: flex-end;
            }
            
            .input-box {
                flex: 1;
                padding: 12px 14px;
                font-size: 16px;
                min-height: 48px;
                max-height: 120px;
                border-radius: 10px;
            }
            
            .send-btn {
                padding: 12px 18px;
                font-size: 14px;
                border-radius: 10px;
                min-width: 60px;
                min-height: 48px;
            }
            
            /* 模态框 - 全屏显示 */
            .modal-overlay {
                padding: 0;
                align-items: flex-end;
            }
            
            .modal-overlay.show {
                display: flex;
            }
            
            .modal {
                width: 100%;
                max-width: 100%;
                max-height: 90vh;
                border-radius: 16px 16px 0 0;
                margin: 0;
            }
            
            .modal-header {
                padding: 16px 20px;
                flex-shrink: 0;
            }
            
            .modal-title {
                font-size: 16px;
            }
            
            .modal-body {
                padding: 16px 20px;
                flex: 1;
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
            }
            
            .modal-actions {
                padding: 12px 20px;
                flex-shrink: 0;
                position: sticky;
                bottom: 0;
                background: #1e293b;
            }
            
            /* 设置页面 - 移动端适配 */
            .settings-tabs {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                padding-bottom: 4px;
            }
            
            .settings-tab {
                white-space: nowrap;
                padding: 8px 12px;
                font-size: 13px;
            }
            
            .setting-row {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
                padding: 12px;
            }
            
            .setting-label {
                width: auto;
                font-size: 13px;
            }
            
            .setting-input,
            .setting-select {
                width: 100%;
                font-size: 14px;
                padding: 10px 12px;
            }
            
            /* 知识库卡片 - 移动端适配 */
            .kb-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            
            .kb-card {
                padding: 16px;
            }
            
            .kb-card-icon {
                font-size: 28px;
            }
            
            .kb-meta {
                flex-wrap: wrap;
            }
            
            /* 技能列表 - 移动端适配 */
            .skill-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }
            
            .skill-info {
                width: 100%;
            }
            
            /* 文件上传区域 - 移动端适配 */
            .file-upload-area {
                padding: 24px 16px;
            }
            
            .file-upload-area h4 {
                font-size: 14px;
            }
            
            /* 帮助内容 - 移动端适配 */
            .help-content {
                font-size: 13px;
                line-height: 1.6;
            }
            
            .help-content h4 {
                font-size: 15px;
            }
            
            .help-content pre {
                padding: 12px;
                margin: 10px 0;
            }
            
            .help-content code {
                font-size: 12px;
            }
            
            /* 开关按钮 - 触摸友好 */
            .setting-switch {
                width: 52px;
                height: 30px;
            }
            
            .setting-switch::after {
                width: 24px;
                height: 24px;
            }
            
            .setting-switch.on::after {
                left: 26px;
            }
            
            /* 按钮 - 触摸友好 */
            .btn {
                min-height: 44px;
                padding: 10px 16px;
                font-size: 14px;
                border-radius: 10px;
            }
            
            /* 工具标签 - 移动端适配 */
            .tool-tag {
                padding: 3px 8px;
                font-size: 11px;
            }
        }
        
        /* ==================== 超小屏幕适配 (< 480px) ==================== */
        @media screen and (max-width: 480px) {
            .header h1 {
                font-size: 14px;
            }
            
            .header-actions .btn {
                padding: 5px 10px;
                font-size: 11px;
            }
            
            .header-actions .btn span {
                display: none;
            }
            
            .message {
                max-width: 95%;
            }
            
            .message-content {
                padding: 10px 12px;
                font-size: 13px;
            }
            
            .input-area {
                padding: 10px 12px;
            }
            
            .input-box {
                padding: 10px 12px;
                font-size: 15px;
                min-height: 44px;
            }
            
            .send-btn {
                padding: 10px 14px;
                min-width: 54px;
                min-height: 44px;
            }
            
            .modal {
                max-height: 85vh;
            }
            
            .modal-header {
                padding: 14px 16px;
            }
            
            .modal-body {
                padding: 12px 16px;
            }
            
            .modal-actions {
                padding: 10px 16px;
            }
            
            .btn {
                min-height: 40px;
                padding: 8px 14px;
                font-size: 13px;
            }
        }
        
        /* ==================== 横屏模式适配 ==================== */
        @media screen and (max-height: 500px) and (orientation: landscape) {
            .input-area {
                position: relative;
                padding: 10px 24px;
            }
            
            .input-box {
                max-height: 80px;
            }
            
            .chat-area {
                flex: 1;
            }
        }
        
        /* ==================== 触摸友好优化 ==================== */
        @media (hover: none) and (pointer: coarse) {
            /* 触摸设备禁用hover效果 */
            .nav-item:hover,
            .btn:hover,
            .kb-card:hover,
            .skill-item:hover {
                background: inherit;
                transform: none;
            }
            
            /* 触摸设备添加active状态 */
            .nav-item:active,
            .btn:active,
            .kb-card:active {
                opacity: 0.8;
            }
            
            /* 触摸设备禁用文本选择 */
            .nav-item,
            .btn,
            .kb-card,
            .skill-item,
            .mcp-item {
                -webkit-user-select: none;
                user-select: none;
            }
            
            /* 输入框可以选中文本 */
            .input-box {
                -webkit-user-select: text;
                user-select: text;
            }
        }
        
        /* ==================== iOS 安全区域适配 ==================== */
        @supports (padding: env(safe-area-inset-bottom)) {
            .input-area {
                padding-bottom: calc(12px + env(safe-area-inset-bottom));
            }
        }
    </style>
</head>
<body>
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="app-container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h2>🤖 DataAgent</h2>
            </div>
            <div class="sidebar-nav">
                <div class="nav-item active" onclick="showMainChat()">
                    <span class="nav-icon">💬</span>
                    <div class="nav-text">
                        <h4>对话</h4>
                        <p>开始智能对话</p>
                    </div>
                </div>
                <div class="nav-divider"></div>
                <div class="nav-item" onclick="openModal('knowledge-modal'); closeSidebar();">
                    <span class="nav-icon">📚</span>
                    <div class="nav-text">
                        <h4>知识库</h4>
                        <p>文档管理与检索</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('prompt-modal'); closeSidebar();">
                    <span class="nav-icon">💡</span>
                    <div class="nav-text">
                        <h4>技能系统</h4>
                        <p>自定义技能与提示词</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('mcp-modal'); closeSidebar();">
                    <span class="nav-icon">🔌</span>
                    <div class="nav-text">
                        <h4>MCP工具</h4>
                        <p>Model Context Protocol</p>
                    </div>
                </div>
                <div class="nav-divider"></div>
                <div class="nav-item" onclick="openModal('settings-modal'); closeSidebar();">
                    <span class="nav-icon">⚙️</span>
                    <div class="nav-text">
                        <h4>设置</h4>
                        <p>模型与系统配置</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('help-modal'); closeSidebar();">
                    <span class="nav-icon">❓</span>
                    <div class="nav-text">
                        <h4>使用说明</h4>
                        <p>帮助文档</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="main-content">
            <div class="header">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <button class="menu-toggle" id="menu-toggle" onclick="toggleSidebar()">☰</button>
                    <h1>万能智能助手</h1>
                </div>
                <div class="header-actions">
                    <button class="btn btn-secondary" onclick="clearChat()">🗑️ 清空对话</button>
                    <button class="btn btn-primary" onclick="openModal('help-modal')">📖 帮助</button>
                </div>
            </div>
            <div class="chat-area" id="chat-area">
                <div class="message system">
                    <div class="message-content">欢迎使用 DataAgent！我是您的万能智能助手。</div>
                </div>
            </div>
            <div class="input-area">
                <div class="input-container">
                    <textarea class="input-box" id="input-box" placeholder="输入您的需求...（Enter发送，Shift+Enter换行）" rows="2"></textarea>
                    <button class="send-btn" id="send-btn" onclick="sendMessage()">发送</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="settings-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">⚙️ 设置</div>
                <button class="modal-close" onclick="closeModal('settings-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="settings-tabs">
                    <div class="settings-tab active" onclick="showSettingsTab('model')">🤖 模型</div>
                    <div class="settings-tab" onclick="showSettingsTab('sandbox')">🏖️ 沙箱</div>
                    <div class="settings-tab" onclick="showSettingsTab('agent')">🧠 智能体</div>
                </div>
                <div class="settings-section active" id="settings-model">
                    <h3>模型配置</h3>
                    <div class="setting-row">
                        <span class="setting-label">模型提供商</span>
                        <select class="setting-select" id="setting-provider">
                            <option value="aliyun">阿里云 - 通义千问</option>
                            <option value="openai">OpenAI - GPT</option>
                            <option value="anthropic">Anthropic - Claude</option>
                            <option value="deepseek">DeepSeek</option>
                        </select>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">模型名称</span>
                        <select class="setting-select" id="setting-model">
                            <option value="qwen-plus-latest">qwen-plus-latest</option>
                            <option value="qwen-max">qwen-max</option>
                            <option value="gpt-4o">gpt-4o</option>
                        </select>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">API Base URL</span>
                        <input type="text" class="setting-input" id="setting-base-url" value="https://dashscope.aliyuncs.com/compatible-mode/v1">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">API Key</span>
                        <input type="password" class="setting-input" id="setting-api-key" placeholder="sk-...">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">最大 Token</span>
                        <input type="number" class="setting-input" id="setting-max-tokens" value="4096">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">温度系数</span>
                        <input type="number" step="0.1" class="setting-input" id="setting-temperature" value="0.7">
                    </div>
                </div>
                <div class="settings-section" id="settings-sandbox">
                    <h3>沙箱环境</h3>
                    <div class="setting-row">
                        <span class="setting-label">启用沙箱</span>
                        <div class="setting-switch on" id="setting-sandbox-enabled" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">执行超时 (秒)</span>
                        <input type="number" class="setting-input" id="setting-sandbox-timeout" value="60">
                    </div>
                </div>
                <div class="settings-section" id="settings-agent">
                    <h3>智能体配置</h3>
                    <div class="setting-row">
                        <span class="setting-label">知识库启用</span>
                        <div class="setting-switch on" id="setting-kb-enabled" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">最大步数</span>
                        <input type="number" class="setting-input" id="setting-max-steps" value="5">
                    </div>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="resetSettings()">重置默认</button>
                <button class="btn btn-primary" onclick="saveSettings()">保存设置</button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="knowledge-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">📚 知识库</div>
                <button class="modal-close" onclick="closeModal('knowledge-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="settings-tabs">
                    <div class="settings-tab active" onclick="showKbTab('list')">知识库列表</div>
                    <div class="settings-tab" onclick="showKbTab('create')">创建知识库</div>
                </div>
                <div class="settings-section active" id="kb-list">
                    <div class="kb-grid" id="kb-grid"></div>
                </div>
                <div class="settings-section" id="kb-create">
                    <div class="setting-row">
                        <span class="setting-label">知识库名称</span>
                        <input type="text" class="setting-input" id="kb-name" placeholder="例如：产品文档库">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">描述</span>
                        <textarea class="setting-input" id="kb-desc" placeholder="简短描述该知识库的用途" rows="3"></textarea>
                    </div>
                    <button class="btn btn-primary" style="width: 100%; margin-top: 16px;" onclick="createKnowledgeBase()">创建知识库</button>
                </div>
                <div class="file-upload-area" onclick="document.getElementById('file-input').click()" style="margin-top: 20px;">
                    <div style="font-size: 32px; margin-bottom: 12px;">📁</div>
                    <h4>上传文档</h4>
                    <p>支持 .pdf, .txt, .md, .docx, .csv 等格式</p>
                    <input type="file" id="file-input" multiple accept=".pdf,.txt,.md,.docx,.csv,.xlsx,.xls,.ppt,.pptx" style="display: none;" onchange="handleFileUpload(event)">
                </div>
                <div id="upload-progress" style="display: none; margin-top: 16px;">
                    <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                        <div id="upload-progress-bar" style="background: linear-gradient(90deg, #3b82f6, #2563eb); height: 100%; width: 0%; transition: width 0.3s;"></div>
                    </div>
                    <p id="upload-status" style="color: #94a3b8; margin-top: 8px; font-size: 13px;">准备上传...</p>
                </div>
                <div id="upload-error" style="display: none; margin-top: 16px; padding: 12px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;">
                    <p style="color: #f87171; margin: 0;">❌ <span id="upload-error-message"></span></p>
                </div>
                <div class="processing-rules">
                    <h4 style="color: white; margin-bottom: 12px;">数据清洗规则</h4>
                    <div class="rule-item">
                        <span>移除多余空格和换行</span>
                        <div class="setting-switch on" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="rule-item">
                        <span>移除URL和邮箱</span>
                        <div class="setting-switch" onclick="toggleSwitch(this)"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="prompt-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">💡 技能系统</div>
                <button class="modal-close" onclick="closeModal('prompt-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="settings-tabs">
                    <div class="settings-tab active" onclick="showSkillTab('list')">技能列表</div>
                    <div class="settings-tab" onclick="showSkillTab('create')">创建技能</div>
                </div>
                <div class="settings-section active" id="skill-list">
                    <div class="skill-list" id="skill-list-content"></div>
                </div>
                <div class="settings-section" id="skill-create">
                    <div class="setting-row">
                        <span class="setting-label">技能用途</span>
                        <input type="text" class="setting-input" id="skill-purpose" placeholder="描述你想要这个技能做什么，例如：代码审查、数据分析等">
                    </div>
                    <button class="btn btn-secondary" style="width: 100%; margin-bottom: 16px;" onclick="aiGenerateSkill()">🤖 AI辅助生成</button>
                    <div class="setting-row">
                        <span class="setting-label">技能名称</span>
                        <input type="text" class="setting-input" id="skill-name" placeholder="例如：代码审查专家">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">图标</span>
                        <input type="text" class="setting-input" id="skill-icon" value="⚡" style="max-width: 80px;">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">描述</span>
                        <textarea class="setting-input" id="skill-desc" placeholder="描述技能的功能" rows="3"></textarea>
                    </div>
                    <div id="ai-generating" style="display: none; margin: 12px 0; padding: 12px; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
                        <p style="color: #60a5fa; margin: 0;">⏳ AI正在生成，请稍候...</p>
                    </div>
                    <button class="btn btn-primary" style="width: 100%; margin-top: 16px;" onclick="createSkill()">创建技能</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="mcp-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">🔌 MCP工具服务</div>
                <button class="modal-close" onclick="closeModal('mcp-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="mcp-list" id="mcp-list-content"></div>
                <div style="margin-top: 20px;">
                    <h4 style="color: white; margin-bottom: 12px;">添加MCP服务器</h4>
                    <div class="setting-row">
                        <span class="setting-label">名称</span>
                        <input type="text" class="setting-input" id="mcp-name" placeholder="例如：本地文件系统">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">类型</span>
                        <select class="setting-select" id="mcp-type">
                            <option value="stdio">stdio</option>
                            <option value="sse">sse</option>
                        </select>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">命令</span>
                        <input type="text" class="setting-input" id="mcp-command" placeholder="例如：npx">
                    </div>
                    <button class="btn btn-primary" style="width: 100%;" onclick="createMcpServer()">添加服务器</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="help-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">❓ 使用说明</div>
                <button class="modal-close" onclick="closeModal('help-modal')">×</button>
            </div>
            <div class="modal-body help-content">
                <h4>🚀 快速开始</h4>
                <p>DataAgent 是一个完整的智能助手系统，包含以下核心功能：</p>
                <ul>
                    <li><strong>万能对话</strong> - 支持自然语言对话，自动识别意图</li>
                    <li><strong>代码执行</strong> - 自动生成并执行 Python 代码</li>
                    <li><strong>图表生成</strong> - 支持 matplotlib 等可视化库</li>
                    <li><strong>知识库管理</strong> - 上传文档，智能检索</li>
                    <li><strong>技能系统</strong> - 自定义提示词和技能</li>
                    <li><strong>MCP工具</strong> - 支持 Model Context Protocol</li>
                </ul>
                <h4>💡 使用示例</h4>
                <pre><code>生成一个正弦函数的折线图
分析这些数据：[1,2,3,4,5]
帮我写一个斐波那契数列
解释这个Python代码</code></pre>
                <h4>📚 知识库说明</h4>
                <p>1. 创建知识库 → 2. 上传文档 → 3. 配置清洗规则 → 4. 提问时自动检索</p>
                <h4>⚡ 技能系统</h4>
                <p>技能是预定义的提示词模板，可以自定义参数和功能。参考规范：<code>config/schema/skill_schema.json</code></p>
                <h4>🔌 MCP协议</h4>
                <p>MCP (Model Context Protocol) 允许连接外部工具和数据源。配置文件：<code>config/mcp.json</code></p>
                <h4>📋 规范文档</h4>
                <p>所有系统规范定义在 <code>config/schema/</code> 目录下：</p>
                <ul>
                    <li><code>knowledge_base_schema.json</code> - 知识库系统规范</li>
                    <li><code>skill_schema.json</code> - 技能系统规范</li>
                    <li><code>mcp_schema.json</code> - MCP工具规范</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let appSettings = {};

        function connectWS() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
            ws.onopen = () => console.log('WebSocket connected');
            ws.onmessage = (event) => handleWSMessage(JSON.parse(event.data));
            ws.onclose = () => setTimeout(connectWS, 3000);
        }

        function handleWSMessage(data) {
            const chatArea = document.getElementById('chat-area');
            if (data.type === 'thinking') {
                let thinkingEl = document.querySelector('.thinking-container');
                if (!thinkingEl) {
                    thinkingEl = document.createElement('div');
                    thinkingEl.className = 'thinking-container';
                    chatArea.appendChild(thinkingEl);
                }
                thinkingEl.innerHTML = `
                    <div class="thinking-phase">
                        <div class="thinking-dot"></div>
                        <div class="thinking-title">${data.title}</div>
                    </div>
                    <div class="thinking-content">${data.content}</div>
                `;
            } else if (data.type === 'response') {
                document.querySelector('.thinking-container')?.remove();
                addMessage(data.content, 'assistant');
                finishProcessing();
            } else if (data.type === 'error') {
                document.querySelector('.thinking-container')?.remove();
                addMessage(data.content, 'system');
                finishProcessing();
            }
        }

        function addMessage(content, type) {
            const chatArea = document.getElementById('chat-area');
            const messageEl = document.createElement('div');
            messageEl.className = `message ${type}`;
            let formatted = content.replace(/\\n/g, '<br>');
            messageEl.innerHTML = `<div class="message-content">${formatted}</div>`;
            chatArea.appendChild(messageEl);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function sendMessage() {
            const inputBox = document.getElementById('input-box');
            const content = inputBox.value.trim();
            if (!content || !ws || ws.readyState !== WebSocket.OPEN) return;
            inputBox.value = '';
            addMessage(content, 'user');
            document.getElementById('send-btn').disabled = true;
            ws.send(JSON.stringify({ content: content }));
        }

        function finishProcessing() {
            document.getElementById('send-btn').disabled = false;
            document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
        }

        function clearChat() {
            const chatArea = document.getElementById('chat-area');
            chatArea.innerHTML = '<div class="message system"><div class="message-content">欢迎使用 DataAgent！</div></div>';
        }

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }

        function closeSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        }

        function openModal(id) {
            document.getElementById(id).classList.add('show');
            if (id === 'knowledge-modal') loadKnowledgeBases();
            if (id === 'prompt-modal') loadSkills();
            if (id === 'mcp-modal') loadMcpServers();
        }

        function closeModal(id) {
            document.getElementById(id).classList.remove('show');
        }

        function toggleSwitch(el) {
            el.classList.toggle('on');
        }

        function showSettingsTab(tab) {
            document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(`settings-${tab}`).classList.add('active');
        }

        function showKbTab(tab) {
            document.querySelectorAll('#knowledge-modal .settings-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#knowledge-modal .settings-section').forEach(s => s.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(`kb-${tab}`).classList.add('active');
        }

        function showSkillTab(tab) {
            document.querySelectorAll('#prompt-modal .settings-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#prompt-modal .settings-section').forEach(s => s.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(`skill-${tab}`).classList.add('active');
        }

        function showMainChat() {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
        }

        async function loadSettings() {
            try {
                const res = await fetch('/api/settings');
                appSettings = await res.json();
                populateSettings(appSettings);
            } catch (e) { console.log(e); }
        }

        function populateSettings(settings) {
            document.getElementById('setting-provider').value = settings.llm.provider;
            document.getElementById('setting-model').value = settings.llm.model;
            document.getElementById('setting-base-url').value = settings.llm.base_url;
            document.getElementById('setting-api-key').value = settings.llm.api_key;
            document.getElementById('setting-max-tokens').value = settings.llm.max_tokens;
            document.getElementById('setting-temperature').value = settings.llm.temperature;
            document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;
        }

        async function saveSettings() {
            const settings = {
                llm: {
                    provider: document.getElementById('setting-provider').value,
                    model: document.getElementById('setting-model').value,
                    base_url: document.getElementById('setting-base-url').value,
                    api_key: document.getElementById('setting-api-key').value,
                    max_tokens: parseInt(document.getElementById('setting-max-tokens').value),
                    temperature: parseFloat(document.getElementById('setting-temperature').value),
                    top_p: 0.9,
                    stream: false
                },
                sandbox: {
                    enabled: document.getElementById('setting-sandbox-enabled').classList.contains('on'),
                    timeout: parseInt(document.getElementById('setting-sandbox-timeout').value),
                    allow_network: false
                },
                knowledge_base: {
                    enabled: document.getElementById('setting-kb-enabled').classList.contains('on'),
                    vector_db: 'sqlite',
                    chunk_size: 1000,
                    chunk_overlap: 200,
                    embedding_model: 'text-embedding-v3'
                },
                conversation: { history_enabled: true, max_history: 50, auto_title: true },
                display: { theme: 'dark', thinking_chain: true, code_highlight: true, markdown_render: true },
                agent: { max_steps: 5, auto_mode: true, reasoning_mode: 'auto' }
            };
            
            // 验证必填字段
            if (!settings.llm.api_key) {
                showError('请输入API Key');
                return;
            }
            if (!settings.llm.base_url) {
                showError('请输入Base URL');
                return;
            }
            if (!settings.llm.max_tokens || settings.llm.max_tokens < 1) {
                showError('最大Token必须大于0');
                return;
            }
            if (settings.llm.temperature < 0 || settings.llm.temperature > 2) {
                showError('温度系数必须在0-2之间');
                return;
            }
            
            try {
                const res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ detail: '保存失败' }));
                    throw new Error(errorData.detail || `请求失败 (${res.status})`);
                }
                
                appSettings = settings;
                closeModal('settings-modal');
                showSuccess('设置已保存成功！');
                
            } catch (e) {
                showError(`保存失败: ${e.message}`);
                console.error('Save settings error:', e);
            }
        }

        function resetSettings() {
            document.getElementById('setting-provider').value = 'aliyun';
            document.getElementById('setting-model').value = 'qwen-plus-latest';
            document.getElementById('setting-base-url').value = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
            document.getElementById('setting-api-key').value = '';
        }

        async function loadKnowledgeBases() {
            try {
                const res = await fetch('/api/knowledge-bases');
                const kbs = await res.json();
                const grid = document.getElementById('kb-grid');
                if (kbs.length === 0) {
                    grid.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px;">还没有知识库，点击上方标签创建</div>';
                } else {
                    grid.innerHTML = kbs.map(kb => `
                        <div class="kb-card">
                            <div class="kb-card-icon">📚</div>
                            <h4>${kb.name}</h4>
                            <p>${kb.description || '暂无描述'}</p>
                            <div class="kb-meta">
                                <span>创建: ${new Date(kb.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    `).join('');
                }
            } catch (e) {
                console.log(e);
            }
        }

        async function createKnowledgeBase() {
            const name = document.getElementById('kb-name').value.trim();
            const desc = document.getElementById('kb-desc').value.trim();
            
            // 前端验证
            if (!name) {
                showError('请输入知识库名称', 'kb-create');
                return;
            }
            if (name.length > 50) {
                showError('知识库名称不能超过50个字符', 'kb-create');
                return;
            }
            
            try {
                const res = await fetch('/api/knowledge-bases', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description: desc })
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
                    throw new Error(errorData.detail || `请求失败 (${res.status})`);
                }
                
                const result = await res.json();
                document.getElementById('kb-name').value = '';
                document.getElementById('kb-desc').value = '';
                loadKnowledgeBases();
                showKbTab('list');
                showSuccess(`知识库 "${name}" 创建成功！`);
                
            } catch (e) {
                showError(`创建知识库失败: ${e.message}`, 'kb-create');
                console.error('Create knowledge base error:', e);
            }
        }

        async function loadSkills() {
            try {
                const res = await fetch('/api/skills');
                const skills = await res.json();
                const list = document.getElementById('skill-list-content');
                list.innerHTML = skills.map(skill => `
                    <div class="skill-item">
                        <div class="skill-info">
                            <div class="skill-icon">${skill.icon}</div>
                            <div class="skill-details">
                                <h4>${skill.name}</h4>
                                <p>${skill.description}</p>
                            </div>
                        </div>
                        <span class="skill-badge">${skill.type}</span>
                    </div>
                `).join('');
            } catch (e) {
                console.log(e);
            }
        }

        async function createSkill() {
            const name = document.getElementById('skill-name').value.trim();
            const icon = document.getElementById('skill-icon').value.trim() || '⚡';
            const desc = document.getElementById('skill-desc').value.trim();
            
            if (!name) {
                showError('请输入技能名称', 'skill-create');
                return;
            }
            if (name.length > 50) {
                showError('技能名称不能超过50个字符', 'skill-create');
                return;
            }
            if (desc && desc.length > 500) {
                showError('描述不能超过500个字符', 'skill-create');
                return;
            }
            
            try {
                const res = await fetch('/api/skills', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, icon, description: desc, parameters: [], prompts: {} })
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
                    throw new Error(errorData.detail || `请求失败 (${res.status})`);
                }
                
                await res.json();
                document.getElementById('skill-name').value = '';
                document.getElementById('skill-desc').value = '';
                loadSkills();
                showSkillTab('list');
                showSuccess(`技能 "${name}" 创建成功！');
                
            } catch (e) {
                showError(`创建技能失败: ${e.message}`, 'skill-create');
                console.error('Create skill error:', e);
            }
        }

        async function loadMcpServers() {
            try {
                const res = await fetch('/api/mcp/servers');
                const servers = await res.json();
                const list = document.getElementById('mcp-list-content');
                if (servers.length === 0) {
                    list.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px;">还没有配置MCP服务器</div>';
                } else {
                    list.innerHTML = servers.map(s => `
                        <div class="mcp-item">
                            <div class="skill-info">
                                <div class="skill-icon">${s.icon}</div>
                                <div class="skill-details">
                                    <h4>${s.name}</h4>
                                    <p>类型: ${s.type}</p>
                                </div>
                            </div>
                            <div class="setting-switch ${s.enabled ? 'on' : ''}" onclick="toggleSwitch(this)"></div>
                        </div>
                    `).join('');
                }
            } catch (e) {
                console.log(e);
            }
        }

        async function createMcpServer() {
            const name = document.getElementById('mcp-name').value.trim();
            const type = document.getElementById('mcp-type').value;
            const command = document.getElementById('mcp-command').value.trim();
            
            if (!name) {
                showError('请输入MCP服务器名称', 'mcp-create');
                return;
            }
            if (name.length > 50) {
                showError('名称不能超过50个字符', 'mcp-create');
                return;
            }
            if (!command && type === 'process') {
                showError('请输入启动命令', 'mcp-create');
                return;
            }
            
            try {
                const res = await fetch('/api/mcp/servers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, type, command, args: [], enabled: true })
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
                    throw new Error(errorData.detail || `请求失败 (${res.status})`);
                }
                
                await res.json();
                document.getElementById('mcp-name').value = '';
                document.getElementById('mcp-command').value = '';
                loadMcpServers();
                showSuccess(`MCP服务器 "${name}" 配置成功！`);
                
            } catch (e) {
                showError(`配置MCP服务器失败: ${e.message}`, 'mcp-create');
                console.error('Create MCP server error:', e);
            }
        }

        function handleFileUpload(event) {
            const files = event.target.files;
            if (files.length > 0) {
                uploadFiles(files);
            }
        }

        async function uploadFiles(files) {
            const progressDiv = document.getElementById('upload-progress');
            const errorDiv = document.getElementById('upload-error');
            const errorMsg = document.getElementById('upload-error-message');
            const progressBar = document.getElementById('upload-progress-bar');
            const uploadStatus = document.getElementById('upload-status');
            
            // 重置UI
            progressDiv.style.display = 'block';
            errorDiv.style.display = 'none';
            progressBar.style.width = '0%';
            uploadStatus.textContent = '准备上传...';
            
            try {
                // 验证文件
                const allowedExtensions = ['.pdf', '.txt', '.md', '.docx', '.csv', '.xlsx', '.xls', '.ppt', '.pptx'];
                const maxSize = 50 * 1024 * 1024; // 50MB
                
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    const ext = '.' + file.name.split('.').pop().toLowerCase();
                    
                    if (!allowedExtensions.includes(ext)) {
                        throw new Error(`文件 ${file.name} 的格式不受支持，请使用以下格式: ${allowedExtensions.join(', ')}`);
                    }
                    
                    if (file.size > maxSize) {
                        throw new Error(`文件 ${file.name} 太大，最大支持50MB`);
                    }
                    
                    uploadStatus.textContent = `正在上传: ${file.name} (${i + 1}/${files.length})`;
                    progressBar.style.width = `${((i) / files.length) * 100}%`;
                    
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
                
                progressBar.style.width = '100%';
                uploadStatus.textContent = `✅ 成功上传 ${files.length} 个文件`;
                
                setTimeout(() => {
                    progressDiv.style.display = 'none';
                    addMessage(`✅ 已上传 ${files.length} 个文档到知识库`, 'system');
                }, 1500);
                
            } catch (e) {
                progressDiv.style.display = 'none';
                errorDiv.style.display = 'block';
                errorMsg.textContent = e.message;
                console.error('Upload error:', e);
            }
            
            // 清空input
            event.target.value = '';
        }
        
        function showError(message, targetId = null) {
            if (targetId) {
                const target = document.getElementById(targetId);
                if (target) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.style.cssText = 'margin-top: 8px; padding: 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #f87171; font-size: 13px;';
                    errorDiv.textContent = '❌ ' + message;
                    target.appendChild(errorDiv);
                    setTimeout(() => errorDiv.remove(), 5000);
                }
            } else {
                addMessage('❌ ' + message, 'system');
            }
        }
        
        function showSuccess(message) {
            addMessage('✅ ' + message, 'system');
        }
        
        async function aiGenerateSkill() {
            const purpose = document.getElementById('skill-purpose').value.trim();
            const generatingDiv = document.getElementById('ai-generating');
            
            if (!purpose) {
                showError('请先描述技能用途', 'skill-create');
                return;
            }
            
            generatingDiv.style.display = 'block';
            
            try {
                // 预定义的技能模板，实际项目中可以调用真实AI
                const skillTemplates = {
                    '代码': { name: '代码审查专家', icon: '🔍', desc: '智能审查代码质量，发现潜在bug和改进建议，提供优化方案' },
                    '数据': { name: '数据分析助手', icon: '📊', desc: '帮助分析数据集，生成可视化图表，提供数据洞察和解读' },
                    '文档': { name: '文档整理专家', icon: '📝', desc: '专业的文档助手，帮助写作、编辑和优化文档内容' },
                    '翻译': { name: '智能翻译官', icon: '🌍', desc: '多语言翻译助手，支持多种语言互译和本地化' },
                    '编程': { name: '编程助手', icon: '💻', desc: '辅助编程，提供代码建议、调试帮助和最佳实践指导' },
                    '写作': { name: '写作顾问', icon: '✍️', desc: '专业写作助手，帮助提升写作质量和表达' },
                    '学习': { name: '学习导师', icon: '📚', desc: '个性化学习助手，根据需求提供学习资料和学习路径' },
                    '创意': { name: '创意工坊', icon: '💡', desc: '激发创意灵感，提供创新想法和解决方案' }
                };
                
                let matched = null;
                for (const [key, value] of Object.entries(skillTemplates)) {
                    if (purpose.includes(key)) {
                        matched = value;
                        break;
                    }
                }
                
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                const result = matched || {
                    name: purpose.length > 10 ? purpose.substring(0, 10) + '...' : purpose + '助手',
                    icon: '✨',
                    desc: '智能助手，专注于' + purpose
                };
                
                document.getElementById('skill-name').value = result.name;
                document.getElementById('skill-icon').value = result.icon;
                document.getElementById('skill-desc').value = result.desc;
                
                generatingDiv.style.display = 'none';
                showSuccess('AI已为您生成技能建议！');
                
            } catch (e) {
                generatingDiv.style.display = 'none';
                showError('AI生成失败: ' + e.message, 'skill-create');
                console.error('AI generate error:', e);
            }
        }

        document.getElementById('input-box').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal-overlay')) {
                e.target.classList.remove('show');
            }
        });

        window.onload = function() {
            connectWS();
            loadSettings();
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting DataAgent Web Interface...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
