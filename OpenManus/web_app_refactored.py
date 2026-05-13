from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import asyncio
import uuid
import datetime
import os
import aiofiles
import shutil

from web.models import Settings, KnowledgeBase, Document, ProcessingRule, Skill, MCPServer
from web.storage import (
    get_settings, save_settings,
    get_knowledge_bases, save_knowledge_bases,
    get_skills, save_skills,
    get_mcp_servers, save_mcp_servers,
    initialize_storage
)
from web.services import execute_python, call_llm, clean_text, run_universal_agent

# 泰迪杯B题功能
try:
    from web.tidycup import FullTidyCupPipeline, FullNL2SQLPipeline
    TIDYCUP_AVAILABLE = True
except ImportError:
    TIDYCUP_AVAILABLE = False

app = FastAPI(
    title="DATA-AI - 万能智能助手",
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

# 全局状态
current_settings: Settings = get_settings()
knowledge_bases_cache = get_knowledge_bases()
documents_cache = {}
skills_cache = get_skills()
mcp_servers_cache = get_mcp_servers()

# 挂载静态文件
static_dir = BASE_DIR / "web" / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 初始化存储
initialize_storage()

# 初始化泰迪杯B题功能
tidycup_pipeline = None
if TIDYCUP_AVAILABLE:
    try:
        db_path = BASE_DIR / "data" / "tidycup.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        tidycup_pipeline = FullTidyCupPipeline(db_path)
        tidycup_pipeline.initialize()
        print("泰迪杯B题功能初始化成功")
    except Exception as e:
        print(f"泰迪杯B题功能初始化失败: {e}")
        TIDYCUP_AVAILABLE = False


@app.get("/", response_class=HTMLResponse)
async def get_index():
    template_dir = BASE_DIR / "web" / "templates"
    index_file = template_dir / "index.html"
    with open(index_file, 'r', encoding='utf-8') as f:
        return f.read()


# API 路由
@app.get("/api/settings")
async def get_settings_endpoint():
    return JSONResponse(get_settings().model_dump())


@app.post("/api/settings")
async def update_settings_endpoint(request: Request):
    global current_settings
    data = await request.json()
    current_settings = Settings(**data)
    save_settings(current_settings)
    return JSONResponse({"success": True, "settings": current_settings.model_dump()})


@app.get("/api/knowledge-bases")
async def list_knowledge_bases_endpoint():
    return JSONResponse([kb.model_dump() for kb in get_knowledge_bases().values()])


@app.post("/api/knowledge-bases")
async def create_knowledge_base_endpoint(request: Request):
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
    kbs = get_knowledge_bases()
    kbs[kb_id] = kb
    save_knowledge_bases(kbs)
    knowledge_bases_cache[kb_id] = kb
    
    data_dir = Path(__file__).parent / "data" / "knowledge_bases" / kb_id
    data_dir.mkdir(exist_ok=True)
    
    return JSONResponse(kb.model_dump())


@app.get("/api/knowledge-bases/{kb_id}")
async def get_knowledge_base_endpoint(kb_id: str):
    kbs = get_knowledge_bases()
    if kb_id not in kbs:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return JSONResponse(kbs[kb_id].model_dump())


async def process_document(doc_id: str, file_path: Path, file_ext: str):
    try:
        content = ""
        
        if file_ext in ['.txt', '.md']:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
        
        elif file_ext == '.csv':
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                content = df.to_string()
            except ImportError:
                content = "需要安装pandas库"
        
        if doc_id in documents_cache:
            documents_cache[doc_id].status = "available"
            documents_cache[doc_id].content = content[:10000] if len(content) > 10000 else content
            
    except Exception as e:
        if doc_id in documents_cache:
            documents_cache[doc_id].status = "failed"
            documents_cache[doc_id].error = str(e)


@app.post("/api/knowledge-bases/{kb_id}/documents")
async def upload_document_endpoint(kb_id: str, file: UploadFile = File(...)):
    kbs = get_knowledge_bases()
    if kb_id not in kbs:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx', '.csv', '.xlsx', '.xls', '.ppt', '.pptx'}
    max_size = 50 * 1024 * 1024
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"
        )
    
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > max_size:
        raise HTTPException(
            status_code=400, 
            detail=f"文件过大: {size / 1024 / 1024:.2f}MB。最大支持 {max_size / 1024 / 1024}MB"
        )
    
    upload_dir = Path(__file__).parent / "data" / "uploads" / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    doc_id = str(uuid.uuid4())
    file_path = upload_dir / f"{doc_id}{file_ext}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        now = datetime.datetime.now().isoformat()
        doc = Document(
            id=doc_id,
            knowledge_base_id=kb_id,
            name=file.filename or "文档",
            data_source_type="upload",
            status="processing",
            file_path=str(file_path),
            created_at=now
        )
        documents_cache[doc_id] = doc
        
        asyncio.create_task(process_document(doc_id, file_path, file_ext))
        
        return JSONResponse({
            **doc.model_dump(),
            "message": f"文件上传成功，正在处理..."
        })
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.get("/api/knowledge-bases/{kb_id}/documents")
async def list_documents_endpoint(kb_id: str):
    kbs = get_knowledge_bases()
    if kb_id not in kbs:
        raise HTTPException(status_code=404, detail="知识库不存在")
    kb_docs = [doc.model_dump() for doc in documents_cache.values() if doc.knowledge_base_id == kb_id]
    return JSONResponse(kb_docs)


@app.get("/api/skills")
async def list_skills_endpoint():
    return JSONResponse([skill.model_dump() for skill in get_skills().values()])


@app.post("/api/skills/generate")
async def generate_skill_endpoint(request: Request):
    data = await request.json()
    purpose = data.get("purpose", "")
    
    if not purpose:
        raise HTTPException(status_code=400, detail="请提供技能用途描述")
    
    settings = get_settings()
    if not settings.llm.get("api_key"):
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")
    
    try:
        prompt = f"""基于以下需求，生成一个AI技能的建议：

需求：{purpose}

请生成一个JSON对象，包含以下字段：
- name: 技能名称（中文，不超过30字）
- icon: 表情符号图标（一个emoji）
- description: 详细描述（中文，100字以内）
- category: 分类（代码/数据/文档/翻译/写作/学习/创意/其他）

只返回JSON，不要其他内容。"""
        
        result_text = await call_llm(prompt, settings)
        
        import re
        import json
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=500, detail="AI返回格式错误")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@app.post("/api/skills")
async def create_skill_endpoint(request: Request):
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
    skill_dict = get_skills()
    skill_dict[skill_id] = skill
    save_skills(skill_dict)
    skills_cache[skill_id] = skill
    return JSONResponse(skill.model_dump())


@app.get("/api/skills/{skill_id}")
async def get_skill_endpoint(skill_id: str):
    skill_dict = get_skills()
    if skill_id not in skill_dict:
        raise HTTPException(status_code=404, detail="技能不存在")
    return JSONResponse(skill_dict[skill_id].model_dump())


@app.post("/api/skills/{skill_id}/use")
async def use_skill_endpoint(skill_id: str, request: Request):
    skill_dict = get_skills()
    if skill_id not in skill_dict:
        raise HTTPException(status_code=404, detail="技能不存在")
    skill = skill_dict[skill_id]
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
    response = await call_llm(prompt, get_settings())
    return JSONResponse({"response": response, "skill": skill.name})


@app.get("/api/mcp/servers")
async def list_mcp_servers_endpoint():
    return JSONResponse([server.model_dump() for server in get_mcp_servers().values()])


@app.post("/api/mcp/servers")
async def create_mcp_server_endpoint(request: Request):
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
    mcp_dict = get_mcp_servers()
    mcp_dict[server_id] = server
    save_mcp_servers(mcp_dict)
    mcp_servers_cache[server_id] = server
    return JSONResponse(server.model_dump())


@app.get("/api/schema/{schema_type}")
async def get_schema_endpoint(schema_type: str):
    config_dir = Path(__file__).parent / "config" / "schema"
    schema_file = config_dir / f"{schema_type}_schema.json"
    if not schema_file.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    with open(schema_file, 'r', encoding='utf-8') as f:
        import json
        return JSONResponse(json.load(f))


# WebSocket 路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("content", "")
            await run_universal_agent(websocket, message, get_settings())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        print(f"Error details: {traceback.format_exc()}")


# ==================== 泰迪杯B题功能路由 ====================

@app.get("/api/tidycup/status")
async def get_tidycup_status():
    """获取泰迪杯B题功能状态"""
    return JSONResponse({
        "available": TIDYCUP_AVAILABLE,
        "version": "1.0.0" if TIDYCUP_AVAILABLE else None
    })


@app.post("/api/tidycup/query")
async def tidycup_query(request: Request):
    """处理泰迪杯B题查询"""
    if not TIDYCUP_AVAILABLE or not tidycup_pipeline:
        raise HTTPException(status_code=501, detail="泰迪杯B题功能未启用")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        result = await tidycup_pipeline.process_complex_query(query)
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")


@app.post("/api/tidycup/nl2sql")
async def tidycup_nl2sql(request: Request):
    """NL2SQL查询"""
    if not TIDYCUP_AVAILABLE or not tidycup_pipeline:
        raise HTTPException(status_code=501, detail="泰迪杯B题功能未启用")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        result = await tidycup_pipeline.nl2sql_pipeline.process_query(query)
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NL2SQL处理失败: {str(e)}")


@app.get("/api/tidycup/sample-queries")
async def get_sample_queries():
    """获取示例查询"""
    samples = [
        "贵州茅台2023年的财务数据",
        "对比贵州茅台和平安银行的业绩",
        "贵州茅台的收入增长趋势",
        "平安银行2023年净利润",
        "白酒行业分析报告"
    ]
    return JSONResponse(samples)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app_refactored:app", host="0.0.0.0", port=8000, reload=True)
