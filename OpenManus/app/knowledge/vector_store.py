"""向量存储模块 - Vector Store Module"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class DocumentChunk:
    """文档片段"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: Optional[float] = None

class VectorStore(ABC):
    """向量存储抽象基类"""

    @abstractmethod
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """添加文档片段"""
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """搜索相似文档"""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[DocumentChunk]:
        """获取单个文档"""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有文档"""
        pass

    @abstractmethod
    def count(self) -> int:
        """返回文档数量"""
        pass

class SimpleVectorStore(VectorStore):
    """简单向量存储实现（基于内存和文件）"""

    def __init__(self, persist_dir: str = "./data/vector_store"):
        self.persist_dir = persist_dir
        self.documents: List[DocumentChunk] = []
        self._ensure_dir()
        self._load_from_disk()

    def _ensure_dir(self):
        os.makedirs(self.persist_dir, exist_ok=True)

    def _generate_id(self, content: str) -> str:
        """基于内容生成唯一ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_to_disk(self):
        """保存到磁盘"""
        data = []
        for doc in self.documents:
            data.append({
                'id': doc.id,
                'content': doc.content,
                'metadata': doc.metadata,
                'embedding': doc.embedding
            })

        with open(os.path.join(self.persist_dir, 'documents.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self):
        """从磁盘加载"""
        try:
            with open(os.path.join(self.persist_dir, 'documents.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    self.documents.append(DocumentChunk(
                        id=item['id'],
                        content=item['content'],
                        metadata=item.get('metadata', {}),
                        embedding=item.get('embedding')
                    ))
        except FileNotFoundError:
            pass

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """添加文档片段"""
        for chunk in chunks:
            if chunk.id not in [doc.id for doc in self.documents]:
                self.documents.append(chunk)
        self._save_to_disk()

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """搜索相似文档"""
        results = []

        for doc in self.documents:
            if doc.embedding:
                score = self._cosine_similarity(query_embedding, doc.embedding)
                doc.score = score
                results.append(doc)

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def get_document(self, doc_id: str) -> Optional[DocumentChunk]:
        """获取单个文档"""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        initial_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.id != doc_id]
        self._save_to_disk()
        return len(self.documents) < initial_count

    def clear(self) -> None:
        """清空所有文档"""
        self.documents = []
        self._save_to_disk()

    def count(self) -> int:
        """返回文档数量"""
        return len(self.documents)

    def get_all_documents(self) -> List[DocumentChunk]:
        """获取所有文档"""
        return self.documents

    def get_metadata_stats(self) -> Dict[str, Any]:
        """获取元数据统计"""
        stats = {
            'total_docs': len(self.documents),
            'sources': set(),
            'types': set(),
            'dates': set()
        }

        for doc in self.documents:
            if 'source' in doc.metadata:
                stats['sources'].add(doc.metadata['source'])
            if 'type' in doc.metadata:
                stats['types'].add(doc.metadata['type'])
            if 'date' in doc.metadata:
                stats['dates'].add(doc.metadata['date'])

        stats['sources'] = list(stats['sources'])
        stats['types'] = list(stats['types'])
        stats['dates'] = list(stats['dates'])

        return stats