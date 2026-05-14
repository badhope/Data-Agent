"""
DataAgent - 知识库路由
包含知识库 CRUD、文档上传/预览/分块/搜索/嵌入等端点
业务逻辑委托给 services 层处理
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from database import (
    knowledge_bases, documents, save_knowledge_bases,
    current_settings
)
from config import KNOWLEDGE_DIR
from models import KnowledgeBase as KBModel, Document as DocModel
from services.knowledge_service import process_document, search_knowledge_base
from services.embedding_service import generate_embeddings
from utils.db_helper import get_kb_or_404
import uuid, datetime, asyncio, shutil
from pathlib import Path
from typing import List

router = APIRouter()


# ==================== 知识库 CRUD ====================

@router.get("/api/knowledge-bases")
async def list_knowledge_bases():
    return JSONResponse([kb.model_dump() for kb in knowledge_bases.values()])


@router.post("/api/knowledge-bases")
async def create_knowledge_base(request: Request):
    data = await request.json()
    kb_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    kb = KBModel(
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


@router.get("/api/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str):
    kb = get_kb_or_404(kb_id)
    return JSONResponse(kb.model_dump())


@router.put("/api/knowledge-bases/{kb_id}")
async def update_knowledge_base(kb_id: str, request: Request):
    kb = get_kb_or_404(kb_id)
    data = await request.json()
    kb.name = data.get("name", kb.name)
    kb.description = data.get("description", kb.description)
    kb.updated_at = datetime.datetime.now().isoformat()
    save_knowledge_bases()
    return JSONResponse(kb.model_dump())


@router.delete("/api/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    get_kb_or_404(kb_id)
    del knowledge_bases[kb_id]
    save_knowledge_bases()
    kb_dir = KNOWLEDGE_DIR / kb_id
    if kb_dir.exists():
        shutil.rmtree(kb_dir)
    docs_to_delete = [doc_id for doc_id, doc in documents.items() if doc.knowledge_base_id == kb_id]
    for doc_id in docs_to_delete:
        del documents[doc_id]
    return JSONResponse({"success": True, "message": "知识库已删除"})


# ==================== 文档上传/管理 ====================

@router.post("/api/knowledge-bases/{kb_id}/documents")
async def upload_document(kb_id: str, file: UploadFile = File(...)):
    get_kb_or_404(kb_id)

    allowed_extensions = {'.pdf', '.txt', '.md', '.docx', '.csv', '.xlsx', '.xls', '.ppt', '.pptx'}
    max_size = 50 * 1024 * 1024  # 50MB

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

    upload_dir = Path("data/uploads") / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = str(uuid.uuid4())
    file_path = upload_dir / f"{doc_id}{file_ext}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        now = datetime.datetime.now().isoformat()
        doc = DocModel(
            id=doc_id,
            knowledge_base_id=kb_id,
            name=file.filename or "文档",
            data_source_type="upload",
            status="processing",
            file_path=str(file_path),
            created_at=now
        )
        documents[doc_id] = doc

        # 委托给 services 层处理文档
        asyncio.create_task(process_document(doc_id, file_path, file_ext))

        return JSONResponse({
            **doc.model_dump(),
            "message": f"文件上传成功，正在处理..."
        })

    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/api/knowledge-bases/{kb_id}/documents/batch")
async def batch_upload_documents(kb_id: str, files: List[UploadFile] = File(...)):
    get_kb_or_404(kb_id)

    results = []
    for file in files:
        try:
            result = await upload_document(kb_id, file)
            results.append({"filename": file.filename, "success": True, "doc": result})
        except Exception as e:
            results.append({"filename": file.filename, "success": False, "error": str(e)})

    return JSONResponse({"results": results})


@router.get("/api/knowledge-bases/{kb_id}/documents")
async def list_documents(kb_id: str):
    get_kb_or_404(kb_id)
    kb_docs = [doc.model_dump() for doc in documents.values() if doc.knowledge_base_id == kb_id]
    return JSONResponse(kb_docs)


@router.delete("/api/knowledge-bases/{kb_id}/documents/{doc_id}")
async def delete_document(kb_id: str, doc_id: str):
    get_kb_or_404(kb_id)
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc = documents[doc_id]
    if doc.knowledge_base_id != kb_id:
        raise HTTPException(status_code=400, detail="文档不属于该知识库")
    del documents[doc_id]
    if doc.file_path and Path(doc.file_path).exists():
        Path(doc.file_path).unlink()
    return JSONResponse({"success": True, "message": "文档已删除"})


# ==================== 文档预览/分块 ====================

@router.get("/api/knowledge-bases/{kb_id}/documents/{doc_id}/preview")
async def preview_document(kb_id: str, doc_id: str):
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc = documents[doc_id]
    return JSONResponse({
        "id": doc.id,
        "name": doc.name,
        "content": doc.content or "",
        "chunks": doc.chunks if hasattr(doc, 'chunks') else [],
        "status": doc.status
    })


@router.get("/api/knowledge-bases/{kb_id}/documents/{doc_id}/chunks")
async def get_document_chunks(kb_id: str, doc_id: str):
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc = documents[doc_id]
    chunks = doc.chunks if hasattr(doc, 'chunks') else []
    return JSONResponse({"chunks": chunks, "total": len(chunks)})


# ==================== 搜索/嵌入 ====================

@router.post("/api/knowledge-bases/{kb_id}/search")
async def search_kb(kb_id: str, request: Request):
    """搜索知识库，委托给 services 层"""
    get_kb_or_404(kb_id)
    data = await request.json()
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    if not query:
        raise HTTPException(status_code=400, detail="请提供搜索查询")

    results = await search_knowledge_base(kb_id, query, top_k)
    return JSONResponse({"results": results, "total": len(results)})


@router.post("/api/knowledge-bases/{kb_id}/embed")
async def generate_kb_embeddings(kb_id: str):
    """为知识库中所有未嵌入的分块生成向量"""
    kb = get_kb_or_404(kb_id)
    api_key = current_settings.llm.get("api_key", "") or ""
    base_url = current_settings.llm.get("base_url", "https://api.openai.com/v1")
    embedding_model = kb.embedding_model or "text-embedding-3-small"

    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置API Key")

    embedded_count = 0
    for doc_id, doc in documents.items():
        if doc.knowledge_base_id != kb_id:
            continue
        if hasattr(doc, 'chunks') and doc.chunks:
            for chunk in doc.chunks:
                if not chunk.get('embedding'):
                    chunk['embedding'] = await generate_embeddings(
                        chunk['content'], api_key, base_url, embedding_model
                    )
                    embedded_count += 1

    return JSONResponse({"success": True, "embedded_chunks": embedded_count})
