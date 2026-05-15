"""FAISS向量存储模块 - 使用FAISS实现高性能向量检索"""
import os
import json
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

@dataclass
class DocumentChunk:
    """文档片段"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: Optional[float] = None

class FAISSVectorStore:
    """基于FAISS的向量存储实现"""
    
    def __init__(self, persist_dir: str = "./data/vector_store", dimension: int = 768):
        self.persist_dir = persist_dir
        self.dimension = dimension
        self.index = None
        self.documents: List[DocumentChunk] = []
        self._ensure_dir()
        
        if FAISS_AVAILABLE:
            self._initialize_index()
            self._load_from_disk()
    
    def _ensure_dir(self):
        os.makedirs(self.persist_dir, exist_ok=True)
    
    def _initialize_index(self):
        """初始化FAISS索引"""
        self.index = faiss.IndexFlatL2(self.dimension)
    
    def _generate_id(self, content: str) -> str:
        """基于内容生成唯一ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _save_to_disk(self):
        """保存到磁盘"""
        if self.index is None:
            return
        
        # 保存FAISS索引
        index_path = os.path.join(self.persist_dir, 'faiss_index')
        faiss.write_index(self.index, index_path)
        
        # 保存文档元数据
        data = []
        for doc in self.documents:
            data.append({
                'id': doc.id,
                'content': doc.content,
                'metadata': doc.metadata
            })
        
        with open(os.path.join(self.persist_dir, 'documents.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_disk(self):
        """从磁盘加载"""
        try:
            # 加载文档元数据
            with open(os.path.join(self.persist_dir, 'documents.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    self.documents.append(DocumentChunk(
                        id=item['id'],
                        content=item['content'],
                        metadata=item.get('metadata', {})
                    ))
            
            # 加载FAISS索引
            index_path = os.path.join(self.persist_dir, 'faiss_index')
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                
        except FileNotFoundError:
            pass
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """添加文档片段"""
        if not FAISS_AVAILABLE:
            for chunk in chunks:
                if chunk.id not in [doc.id for doc in self.documents]:
                    self.documents.append(chunk)
            return
        
        new_chunks = []
        embeddings = []
        
        for chunk in chunks:
            if chunk.id not in [doc.id for doc in self.documents]:
                self.documents.append(chunk)
                new_chunks.append(chunk)
                
                if chunk.embedding is not None:
                    embeddings.append(chunk.embedding)
        
        if embeddings:
            embeddings_np = np.array(embeddings, dtype=np.float32)
            self.index.add(embeddings_np)
        
        self._save_to_disk()
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """搜索相似文档"""
        if not FAISS_AVAILABLE or not query_embedding or len(self.documents) == 0:
            # 回退到简单搜索
            return self._simple_search(query_embedding, top_k)
        
        query_np = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_np, min(top_k, len(self.documents)))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.documents):
                doc = self.documents[idx]
                doc.score = 1 - (distances[0][i] / (2 * self.dimension))
                results.append(doc)
        
        return results
    
    def _simple_search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """简单搜索（回退方案）"""
        if not query_embedding:
            return []
        
        results = []
        for doc in self.documents:
            if doc.embedding:
                score = self._cosine_similarity(query_embedding, doc.embedding)
                doc.score = score
                results.append(doc)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
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
        
        if FAISS_AVAILABLE and self.index is not None:
            self._rebuild_index()
        
        self._save_to_disk()
        return len(self.documents) < initial_count
    
    def _rebuild_index(self):
        """重建索引"""
        self.index = faiss.IndexFlatL2(self.dimension)
        embeddings = []
        for doc in self.documents:
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
        
        if embeddings:
            embeddings_np = np.array(embeddings, dtype=np.float32)
            self.index.add(embeddings_np)
    
    def clear(self) -> None:
        """清空所有文档"""
        self.documents = []
        if FAISS_AVAILABLE:
            self._initialize_index()
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
    
    def batch_search(self, queries: List[List[float]], top_k: int = 5) -> List[List[DocumentChunk]]:
        """批量搜索"""
        if not FAISS_AVAILABLE or not queries:
            return [self.search(query, top_k) for query in queries]
        
        queries_np = np.array(queries, dtype=np.float32)
        distances, indices = self.index.search(queries_np, min(top_k, len(self.documents)))
        
        results = []
        for i in range(len(queries)):
            query_results = []
            for j, idx in enumerate(indices[i]):
                if idx >= 0 and idx < len(self.documents):
                    doc = self.documents[idx]
                    doc.score = 1 - (distances[i][j] / (2 * self.dimension))
                    query_results.append(doc)
            results.append(query_results)
        
        return results
    
    @staticmethod
    def is_available() -> bool:
        """检查FAISS是否可用"""
        return FAISS_AVAILABLE