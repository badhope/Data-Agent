"""知识库API路由"""
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os

router = APIRouter()

# 全局知识库管理器
knowledge_manager = None

def get_knowledge_manager():
    """获取知识库管理器"""
    global knowledge_manager
    if knowledge_manager is None:
        from app.knowledge import KnowledgeManager
        knowledge_manager = KnowledgeManager()
    return knowledge_manager

@router.get("/api/knowledge/bases")
async def list_knowledge_bases():
    """列出所有知识库"""
    km = get_knowledge_manager()
    return JSONResponse(km.list_knowledge_bases())

@router.post("/api/knowledge/bases")
async def create_knowledge_base(request: Request):
    """创建新的知识库"""
    data = await request.json()
    name = data.get('name', 'default')

    km = get_knowledge_manager()
    kb = km.create_knowledge_base(name)

    return JSONResponse({
        'success': True,
        'name': kb.name,
        'document_count': kb.count()
    })

@router.delete("/api/knowledge/bases/{name}")
async def delete_knowledge_base(name: str):
    """删除知识库"""
    km = get_knowledge_manager()
    success = km.delete_knowledge_base(name)

    return JSONResponse({
        'success': success
    })

@router.get("/api/knowledge/bases/{name}/stats")
async def get_knowledge_base_stats(name: str):
    """获取知识库统计信息"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    return JSONResponse(kb.get_stats())

@router.post("/api/knowledge/bases/{name}/documents")
async def add_document_to_knowledge_base(name: str, request: Request):
    """添加文档到知识库"""
    data = await request.json()
    content = data.get('content', '')
    metadata = data.get('metadata', {})

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    doc_id = kb.add_document(content, metadata)

    return JSONResponse({
        'success': True,
        'document_id': doc_id
    })

@router.post("/api/knowledge/bases/{name}/files")
async def upload_files_to_knowledge_base(name: str, files: List[UploadFile] = File(...)):
    """上传文件到知识库"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    results = []
    for file in files:
        # 保存临时文件
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(await file.read())

        # 添加到知识库
        result = kb.add_file(temp_path)
        result['filename'] = file.filename

        # 清理临时文件
        os.remove(temp_path)

        results.append(result)

    return JSONResponse({
        'success': True,
        'results': results
    })

@router.get("/api/knowledge/bases/{name}/documents")
async def get_documents(name: str, page: int = 1, page_size: int = 10):
    """获取知识库中的文档列表"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    documents = kb.get_all_documents()
    total = len(documents)

    start = (page - 1) * page_size
    end = start + page_size
    paginated = documents[start:end]

    return JSONResponse({
        'success': True,
        'documents': paginated,
        'total': total,
        'page': page,
        'page_size': page_size
    })

@router.get("/api/knowledge/bases/{name}/documents/{doc_id}")
async def get_document(name: str, doc_id: str):
    """获取单个文档"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    doc = kb.get_document(doc_id)

    if not doc:
        return JSONResponse({'success': False, 'error': '文档不存在'}, status_code=404)

    return JSONResponse(doc)

@router.delete("/api/knowledge/bases/{name}/documents/{doc_id}")
async def delete_document(name: str, doc_id: str):
    """删除文档"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    success = kb.delete_document(doc_id)

    return JSONResponse({
        'success': success
    })

@router.post("/api/knowledge/bases/{name}/search")
async def search_knowledge_base(name: str, request: Request):
    """搜索知识库"""
    data = await request.json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    results = kb.search(query, top_k)

    return JSONResponse({
        'success': True,
        'results': results,
        'count': len(results)
    })

@router.post("/api/knowledge/bases/{name}/query")
async def query_knowledge_base(name: str, request: Request):
    """查询知识库（问答模式）"""
    data = await request.json()
    question = data.get('question', '')
    llm_config = data.get('llm', None)

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    from app.knowledge import QAEngine

    qa_engine = QAEngine(kb)
    result = await qa_engine.answer(question, llm_config)

    return JSONResponse(result)

@router.post("/api/knowledge/bases/{name}/chat")
async def chat_with_knowledge_base(name: str, request: Request):
    """与知识库对话"""
    data = await request.json()
    question = data.get('question', '')
    llm_config = data.get('llm', None)

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    from app.knowledge import ConversationalQAEngine

    # 简化实现：每次创建新引擎
    qa_engine = ConversationalQAEngine(kb)
    result = await qa_engine.answer(question, llm_config)

    return JSONResponse(result)

@router.post("/api/knowledge/bases/{name}/export")
async def export_knowledge_base(name: str):
    """导出知识库"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    data = kb.export()
    return JSONResponse(data)

@router.post("/api/knowledge/bases/{name}/import")
async def import_to_knowledge_base(name: str, request: Request):
    """导入文档到知识库"""
    data = await request.json()

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    result = kb.import_documents(data)
    return JSONResponse(result)

@router.delete("/api/knowledge/bases/{name}/clear")
async def clear_knowledge_base(name: str):
    """清空知识库"""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': '知识库不存在'}, status_code=404)

    kb.clear()

    return JSONResponse({
        'success': True
    })