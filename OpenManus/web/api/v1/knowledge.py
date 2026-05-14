"""
Knowledge Base API Router
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from pathlib import Path
import shutil
import uuid

from web.models import KnowledgeBase, Document
from web.storage import (
    get_knowledge_bases, save_knowledge_bases,
    get_documents, save_documents
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "knowledge"
DATA_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/bases")
async def list_knowledge_bases():
    """获取所有知识库"""
    bases = get_knowledge_bases()
    return JSONResponse([
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "created_at": kb.created_at,
            "updated_at": kb.updated_at,
            "document_count": len([d for d in get_documents().values() if d.kb_id == kb.id])
        }
        for kb in bases.values()
    ])

@router.post("/bases")
async def create_knowledge_base(request: Dict[str, Any]):
    """创建知识库"""
    name = request.get("name")
    description = request.get("description", "")
    
    if not name:
        raise HTTPException(status_code=400, detail="知识库名称不能为空")
    
    kb = KnowledgeBase(
        id=str(uuid.uuid4()),
        name=name,
        description=description
    )
    
    bases = get_knowledge_bases()
    bases[kb.id] = kb
    save_knowledge_bases(bases)
    
    return JSONResponse(kb.model_dump())

@router.post("/bases/{kb_id}/documents")
async def upload_document(kb_id: str, file: UploadFile = File(...)):
    """上传文档到知识库"""
    bases = get_knowledge_bases()
    if kb_id not in bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 保存文件
    file_extension = Path(file.filename).suffix
    file_id = str(uuid.uuid4())
    file_path = DATA_DIR / f"{file_id}{file_extension}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        doc = Document(
            id=file_id,
            kb_id=kb_id,
            name=file.filename,
            path=str(file_path),
            file_type=file_extension
        )
        
        docs = get_documents()
        docs[doc.id] = doc
        save_documents(docs)
        
        return JSONResponse({"success": True, "document": doc.model_dump()})
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/bases/{kb_id}/documents")
async def list_documents(kb_id: str):
    """获取知识库的所有文档"""
    docs = [
        d.model_dump()
        for d in get_documents().values()
        if d.kb_id == kb_id
    ]
    return JSONResponse(docs)

@router.delete("/bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    bases = get_knowledge_bases()
    if kb_id not in bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 删除相关文档
    docs = get_documents()
    to_delete = [d.id for d in docs.values() if d.kb_id == kb_id]
    for doc_id in to_delete:
        doc = docs.pop(doc_id)
        try:
            Path(doc.path).unlink(missing_ok=True)
        except Exception:
            pass
    
    save_documents(docs)
    
    del bases[kb_id]
    save_knowledge_bases(bases)
    
    return JSONResponse({"success": True})
