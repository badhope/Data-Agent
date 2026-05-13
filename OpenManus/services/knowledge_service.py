"""
DataAgent - 知识库服务
提供文档文本清洗、文件内容提取、文档处理、文本分块和知识库搜索功能
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from database import documents, knowledge_bases, current_settings
from services.embedding_service import generate_embeddings, cosine_similarity


async def clean_text(text: str, rules: dict) -> str:
    """根据预处理规则清洗文本"""
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


async def extract_text_from_file(file_path: Path, file_ext: str) -> str:
    """从文件中提取文本内容（支持 txt/md/csv/pdf/docx）"""
    content = ""

    if file_ext in ('.txt', '.md'):
        import aiofiles
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()

    elif file_ext == '.csv':
        import pandas as pd
        df = pd.read_csv(file_path)
        content = df.to_string()

    elif file_ext == '.pdf':
        try:
            import fitz
            doc = fitz.open(file_path)
            content = "\n".join([page.get_text() for page in doc])
            doc.close()
        except Exception:
            content = "[PDF内容需要安装pymupdf库]"

    elif file_ext == '.docx':
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        except Exception:
            content = "[DOCX内容需要安装python-docx库]"

    return content


async def process_document(doc_id: str, file_path: Path, file_ext: str):
    """处理文档：提取文本、分块、更新状态"""
    try:
        content = await extract_text_from_file(file_path, file_ext)

        if doc_id in documents:
            documents[doc_id].status = "available"
            documents[doc_id].content = content[:100000] if len(content) > 100000 else content
            chunks = split_into_chunks(content, chunk_size=500, overlap=50)
            documents[doc_id].chunks = chunks
            documents[doc_id].chunk_count = len(chunks)

    except Exception as e:
        if doc_id in documents:
            documents[doc_id].status = "failed"
            documents[doc_id].error = str(e)


def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[dict]:
    """将文本按固定大小分块"""
    if not text:
        return []
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        chunks.append({
            "id": chunk_id,
            "content": chunk_text,
            "start": start,
            "end": min(end, len(text))
        })
        chunk_id += 1
        start = end - overlap
        if start >= len(text) - overlap:
            break
    return chunks


async def search_knowledge_base(kb_id: str, query: str, top_k: int = 5) -> List[dict]:
    """在指定知识库中搜索与查询最相关的文本块"""
    if kb_id not in knowledge_bases:
        return []

    kb = knowledge_bases[kb_id]
    results = []

    api_key = current_settings.llm.get("api_key", "") or ""
    base_url = current_settings.llm.get("base_url", "https://api.openai.com/v1")
    embedding_model = kb.embedding_model or "text-embedding-3-small"

    query_embedding = await generate_embeddings(query, api_key, base_url, embedding_model)

    for doc_id, doc in documents.items():
        if doc.knowledge_base_id != kb_id:
            continue
        if not hasattr(doc, 'chunks') or not doc.chunks:
            continue

        for chunk in doc.chunks:
            if not chunk.get('embedding'):
                chunk['embedding'] = await generate_embeddings(
                    chunk['content'], api_key, base_url, embedding_model
                )

            if query_embedding and chunk.get('embedding'):
                score = cosine_similarity(query_embedding, chunk['embedding'])
                results.append({
                    "doc_id": doc_id,
                    "doc_name": doc.name,
                    "chunk_id": chunk['id'],
                    "content": chunk['content'],
                    "score": score
                })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]
