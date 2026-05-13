from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import asyncio
import uuid
import datetime
import os
import tempfile
import shutil
import sys
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any

from web.models import Settings, KnowledgeBase, Document, ProcessingRule, Skill, MCPServer
from web.storage import (
    get_settings, save_settings,
    get_knowledge_bases, save_knowledge_bases,
    get_skills, save_skills,
    get_mcp_servers, save_mcp_servers
)
from web.services import execute_python, call_llm, clean_text, run_universal_agent

router = APIRouter()

# 全局状态
current_settings: Settings = get_settings()
knowledge_bases: Dict[str, KnowledgeBase] = get_knowledge_bases()
documents: Dict[str, Document] = {}
skills: Dict[str, Skill] = get_skills()
mcp_servers: Dict[str, MCPServer] = get_mcp_servers()


@router.get("/api/settings")
async def get_settings_endpoint():
    return JSONResponse(get_settings().model_dump())


@router.post("/api/settings")
async def update_settings_endpoint(request: Request):
    global current_settings
    data = await request.json()
    current_settings = Settings(**data)
    save_settings(current_settings)
    return JSONResponse({"success": True, "settings": current_settings.model_dump()})


@router.get("/api/knowledge-bases")
async def list_knowledge_bases_endpoint():
    return JSONResponse([kb.model_dump() for kb in get_knowledge_bases().values()])


@router.post("/api/knowledge-bases")
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
    knowledge_bases[kb_id] = kb
    
    data_dir = Path(__file__).parent.parent / "data" / "knowledge_bases" / kb_id
    data_dir.mkdir(exist_ok=True)
    
    return JSONResponse(kb.model_dump())


@router.get("/api/knowledge-bases/{kb_id}")
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
        
        if doc_id in documents:
            documents[doc_id].status = "available"
            documents[doc_id].content = content[:10000] if len(content) > 10000 else content
            
    except Exception as e:
        if doc_id in documents:
            documents[doc_id].status = "failed"
            documents[doc_id].error = str(e)


@router.post("/api/knowledge-bases/{kb_id}/documents")
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
    
    upload_dir = Path(__file__).parent.parent / "data" / "uploads" / kb_id
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
        documents[doc_id] = doc
        
        asyncio.create_task(process_document(doc_id, file_path, file_ext))
        
        return JSONResponse({
            **doc.model_dump(),
            "message": f"文件上传成功，正在处理..."
        })
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/api/knowledge-bases/{kb_id}/documents")
async def list_documents_endpoint(kb_id: str):
    kbs = get_knowledge_bases()
    if kb_id not in kbs:
        raise HTTPException(status_code=404, detail="知识库不存在")
    kb_docs = [doc.model_dump() for doc in documents.values() if doc.knowledge_base_id == kb_id]
    return JSONResponse(kb_docs)


@router.get("/api/skills")
async def list_skills_endpoint():
    return JSONResponse([skill.model_dump() for skill in get_skills().values()])


@router.post("/api/skills/generate")
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
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            import json
            result = json.loads(json_match.group())
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=500, detail="AI返回格式错误")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@router.post("/api/skills")
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
    skills[skill_id] = skill
    return JSONResponse(skill.model_dump())


@router.get("/api/skills/{skill_id}")
async def get_skill_endpoint(skill_id: str):
    skill_dict = get_skills()
    if skill_id not in skill_dict:
        raise HTTPException(status_code=404, detail="技能不存在")
    return JSONResponse(skill_dict[skill_id].model_dump())


@router.post("/api/skills/{skill_id}/use")
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


@router.get("/api/mcp/servers")
async def list_mcp_servers_endpoint():
    return JSONResponse([server.model_dump() for server in get_mcp_servers().values()])


@router.post("/api/mcp/servers")
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
    mcp_servers[server_id] = server
    return JSONResponse(server.model_dump())


@router.get("/api/schema/{schema_type}")
async def get_schema_endpoint(schema_type: str):
    config_dir = Path(__file__).parent.parent / "config" / "schema"
    schema_file = config_dir / f"{schema_type}_schema.json"
    if not schema_file.exists():
        raise HTTPException(status_code=404, detail="Schema不存在")
    with open(schema_file, 'r', encoding='utf-8') as f:
        import json
        return JSONResponse(json.load(f))


@router.websocket("/ws")
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
