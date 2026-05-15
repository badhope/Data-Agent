"""知识库模块 - Knowledge Base Module"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from .vector_store import VectorStore, SimpleVectorStore, DocumentChunk
from .document_loader import DocumentLoaderFactory, Document

class KnowledgeBase:
    """知识库类"""

    def __init__(self, name: str = "default", persist_dir: str = "./data/knowledge_base"):
        self.name = name
        self.persist_dir = os.path.join(persist_dir, name)
        self.vector_store = SimpleVectorStore(self.persist_dir)
        self.loader_factory = DocumentLoaderFactory()

        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(self.persist_dir, exist_ok=True)

    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加文档内容"""
        metadata = metadata or {}
        metadata['added_at'] = datetime.now().isoformat()

        chunk = DocumentChunk(
            id=self._generate_id(content),
            content=content,
            metadata=metadata
        )

        self.vector_store.add_documents([chunk])
        return chunk.id

    def add_file(self, file_path: str) -> Dict[str, Any]:
        """添加文件到知识库"""
        if not os.path.exists(file_path):
            return {'success': False, 'error': '文件不存在'}

        try:
            doc = self.loader_factory.load(file_path)
            chunks = doc.chunk()

            results = []
            for i, chunk in enumerate(chunks):
                metadata = doc.metadata.copy()
                metadata['chunk_index'] = i
                metadata['total_chunks'] = len(chunks)
                metadata['added_at'] = datetime.now().isoformat()

                doc_chunk = DocumentChunk(
                    id=self._generate_id(chunk + str(i)),
                    content=chunk,
                    metadata=metadata
                )
                results.append(doc_chunk.id)

            self.vector_store.add_documents([DocumentChunk(
                id=self._generate_id(doc.content),
                content=doc.content,
                metadata=doc.metadata
            )])

            return {
                'success': True,
                'document_name': doc.metadata.get('source', os.path.basename(file_path)),
                'chunks_added': len(results),
                'ids': results,
                'word_count': doc.get_word_count()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """添加多个文件"""
        results = []
        for file_path in file_paths:
            result = self.add_file(file_path)
            results.append(result)
        return results

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """查询知识库"""
        # 简单的字符串匹配搜索（生产环境应使用向量搜索）
        results = []

        documents = self.vector_store.get_all_documents()

        for doc in documents:
            if query.lower() in doc.content.lower():
                # 计算匹配分数（简单实现）
                score = doc.content.lower().count(query.lower()) / len(doc.content.split())
                doc.score = score
                results.append(doc)

        results.sort(key=lambda x: x.score, reverse=True)

        return [self._doc_to_dict(doc) for doc in results[:top_k]]

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识库（使用向量搜索）"""
        # 如果有嵌入向量，使用向量搜索
        documents = self.vector_store.get_all_documents()

        if any(doc.embedding for doc in documents):
            # 简单的基于关键词的搜索作为回退
            return self.query(query, top_k)

        # 回退到简单搜索
        return self.query(query, top_k)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        doc = self.vector_store.get_document(doc_id)
        if doc:
            return self._doc_to_dict(doc)
        return None

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        return self.vector_store.delete_document(doc_id)

    def clear(self) -> None:
        """清空知识库"""
        self.vector_store.clear()

    def count(self) -> int:
        """获取文档数量"""
        return self.vector_store.count()

    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        stats = self.vector_store.get_metadata_stats()
        stats['name'] = self.name
        stats['total_chunks'] = self.count()
        return stats

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档"""
        documents = self.vector_store.get_all_documents()
        return [self._doc_to_dict(doc) for doc in documents]

    def export(self) -> Dict[str, Any]:
        """导出知识库"""
        documents = self.get_all_documents()
        return {
            'name': self.name,
            'exported_at': datetime.now().isoformat(),
            'total_documents': len(documents),
            'documents': documents
        }

    def import_documents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """导入文档"""
        documents = data.get('documents', [])
        added = 0

        for doc in documents:
            self.add_document(
                content=doc.get('content', ''),
                metadata=doc.get('metadata', {})
            )
            added += 1

        return {'success': True, 'documents_added': added}

    def _generate_id(self, content: str) -> str:
        """生成文档ID"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _doc_to_dict(self, doc: DocumentChunk) -> Dict[str, Any]:
        """将文档转换为字典"""
        return {
            'id': doc.id,
            'content': doc.content,
            'metadata': doc.metadata,
            'score': doc.score
        }

class KnowledgeManager:
    """知识库管理器"""

    def __init__(self, base_dir: str = "./data/knowledge_base"):
        self.base_dir = base_dir
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}

        self._ensure_dir()
        self._load_existing_bases()

    def _ensure_dir(self):
        os.makedirs(self.base_dir, exist_ok=True)

    def _load_existing_bases(self):
        """加载已存在的知识库"""
        if os.path.isdir(self.base_dir):
            for item in os.listdir(self.base_dir):
                item_path = os.path.join(self.base_dir, item)
                if os.path.isdir(item_path):
                    self.knowledge_bases[item] = KnowledgeBase(item, self.base_dir)

    def create_knowledge_base(self, name: str) -> KnowledgeBase:
        """创建新的知识库"""
        if name in self.knowledge_bases:
            return self.knowledge_bases[name]

        kb = KnowledgeBase(name, self.base_dir)
        self.knowledge_bases[name] = kb
        return kb

    def get_knowledge_base(self, name: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self.knowledge_bases.get(name)

    def delete_knowledge_base(self, name: str) -> bool:
        """删除知识库"""
        if name not in self.knowledge_bases:
            return False

        kb = self.knowledge_bases[name]
        kb.clear()

        # 删除目录
        import shutil
        try:
            shutil.rmtree(kb.persist_dir)
            del self.knowledge_bases[name]
            return True
        except Exception:
            return False

    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """列出所有知识库"""
        result = []
        for name, kb in self.knowledge_bases.items():
            stats = kb.get_stats()
            result.append({
                'name': name,
                'document_count': stats.get('total_chunks', 0),
                'sources': stats.get('sources', []),
                'types': stats.get('types', [])
            })
        return result

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有知识库的统计信息"""
        stats = {
            'total_knowledge_bases': len(self.knowledge_bases),
            'total_documents': 0,
            'knowledge_bases': []
        }

        for name, kb in self.knowledge_bases.items():
            kb_stats = kb.get_stats()
            stats['total_documents'] += kb_stats.get('total_chunks', 0)
            stats['knowledge_bases'].append({
                'name': name,
                'documents': kb_stats.get('total_chunks', 0)
            })

        return stats