"""LlamaIndex RAG集成 - 企业级检索增强生成"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from llama_index.core import (
        VectorStoreIndex,
        SimpleDirectoryReader,
        StorageContext,
        load_index_from_storage,
        Settings
    )
    from llama_index.llms.openai import OpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

@dataclass
class RAGResult:
    """RAG检索结果"""
    success: bool
    answer: str = ""
    sources: List[Dict] = None
    error: str = ""
    token_usage: Dict = None

class LlamaIndexRAG:
    """基于LlamaIndex的RAG实现"""
    
    def __init__(self, persist_dir: str = "./data/llama_index", model_name: str = "gpt-4o"):
        self.persist_dir = persist_dir
        self.model_name = model_name
        self.index = None
        self._init_settings()
        
        if LLAMA_INDEX_AVAILABLE:
            self._ensure_dir()
            self._load_or_create_index()
    
    def _init_settings(self):
        """初始化LlamaIndex设置"""
        if LLAMA_INDEX_AVAILABLE:
            Settings.llm = OpenAI(model=self.model_name, temperature=0)
            Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    
    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(self.persist_dir, exist_ok=True)
    
    def _load_or_create_index(self):
        """加载或创建索引"""
        if os.path.exists(os.path.join(self.persist_dir, "storage")):
            try:
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                self.index = load_index_from_storage(storage_context)
                print(f"✓ 从磁盘加载索引成功")
            except Exception as e:
                print(f"加载索引失败，创建新索引: {e}")
                self.index = VectorStoreIndex([])
                self.index.storage_context.persist(persist_dir=self.persist_dir)
        else:
            self.index = VectorStoreIndex([])
            self.index.storage_context.persist(persist_dir=self.persist_dir)
    
    def add_documents(self, file_paths: List[str]) -> bool:
        """添加文档到索引"""
        if not LLAMA_INDEX_AVAILABLE:
            return False
        
        try:
            # 加载文档
            documents = SimpleDirectoryReader(input_files=file_paths).load_data()
            
            if not documents:
                print("未加载到任何文档")
                return False
            
            # 添加到索引
            for doc in documents:
                self.index.insert(doc)
            
            # 持久化
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            print(f"✓ 成功添加 {len(documents)} 个文档")
            
            return True
        
        except Exception as e:
            print(f"添加文档失败: {e}")
            return False
    
    def add_text(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """添加文本内容到索引"""
        if not LLAMA_INDEX_AVAILABLE:
            return False
        
        try:
            from llama_index.core import Document
            
            doc = Document(text=text, metadata=metadata or {})
            self.index.insert(doc)
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            
            return True
        
        except Exception as e:
            print(f"添加文本失败: {e}")
            return False
    
    async def query(self, query: str, top_k: int = 3) -> RAGResult:
        """查询索引"""
        if not LLAMA_INDEX_AVAILABLE:
            return RAGResult(
                success=False,
                error="LlamaIndex未安装，请安装: pip install llama-index llama-index-llms-openai llama-index-embeddings-openai"
            )
        
        if self.index is None:
            return RAGResult(
                success=False,
                error="索引未初始化"
            )
        
        try:
            # 创建查询引擎
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                streaming=False
            )
            
            # 执行查询
            response = query_engine.query(query)
            
            # 提取来源信息
            sources = []
            for node in response.source_nodes:
                sources.append({
                    "text": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                    "score": node.score,
                    "metadata": node.metadata
                })
            
            return RAGResult(
                success=True,
                answer=str(response),
                sources=sources,
                token_usage={}
            )
        
        except Exception as e:
            return RAGResult(
                success=False,
                error=f"查询失败: {str(e)}"
            )
    
    def query_sync(self, query: str, top_k: int = 3) -> RAGResult:
        """同步查询"""
        import asyncio
        return asyncio.run(self.query(query, top_k))
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if not LLAMA_INDEX_AVAILABLE or self.index is None:
            return False
        
        try:
            self.index.delete(doc_id)
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def clear(self) -> bool:
        """清空索引"""
        if not LLAMA_INDEX_AVAILABLE:
            return False
        
        try:
            self.index = VectorStoreIndex([])
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            return True
        except Exception as e:
            print(f"清空索引失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        if not LLAMA_INDEX_AVAILABLE or self.index is None:
            return {"error": "LlamaIndex不可用"}
        
        try:
            return {
                "document_count": len(self.index.docstore.docs),
                "persist_dir": self.persist_dir,
                "model_name": self.model_name
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def is_available() -> bool:
        """检查LlamaIndex是否可用"""
        return LLAMA_INDEX_AVAILABLE

# 全局实例
llama_index_rag = None

def get_llama_index_rag(persist_dir: str = "./data/llama_index") -> LlamaIndexRAG:
    """获取全局LlamaIndex RAG实例"""
    global llama_index_rag
    if llama_index_rag is None:
        llama_index_rag = LlamaIndexRAG(persist_dir)
    return llama_index_rag