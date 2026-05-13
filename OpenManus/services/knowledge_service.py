"""
知识库服务
提供文档文本清洗、文档处理和文本分块功能
"""

import re
from pathlib import Path
from typing import List, Dict, Any

import aiofiles

from database import documents


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


async def process_document(doc_id: str, file_path: Path, file_ext: str):
    try:
        content = ""

        if file_ext == '.txt' or file_ext == '.md':
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
            except:
                content = "[PDF内容需要安装pymupdf库]"

        elif file_ext == '.docx':
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            except:
                content = "[DOCX内容需要安装python-docx库]"

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
