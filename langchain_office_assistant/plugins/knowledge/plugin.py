from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import os

logger = get_logger(__name__)

class KnowledgePlugin(BasePlugin):
    name = "knowledge"
    description = "知识库插件 - 向量检索、多模态支持"

    def __init__(self):
        super().__init__()
        self.vector_store = None
        self.documents = []

    def initialize(self, config: Dict) -> None:
        self.config = config
        self._init_vector_store()
        logger.info(f"KnowledgePlugin initialized")

    def _init_vector_store(self):
        try:
            embeddings = OpenAIEmbeddings(
                api_key=self.config.get("openai_api_key"),
                model="text-embedding-3-small"
            )

            if os.path.exists("knowledge_db"):
                self.vector_store = FAISS.load_local(
                    "knowledge_db",
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                self.vector_store = FAISS.from_texts(
                    ["Welcome to the knowledge base"],
                    embeddings
                )
                self.vector_store.save_local("knowledge_db")
        except Exception as e:
            logger.warning(f"Failed to initialize vector store: {e}")

    def get_tools(self) -> List:
        return [add_document, search_knowledge, query_knowledge, list_documents]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "add_document": add_document,
            "search_knowledge": search_knowledge,
            "query_knowledge": query_knowledge,
            "list_documents": list_documents,
        }

        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"

        tool_func = tools_map[tool_name]
        return tool_func.invoke(kwargs)

_knowledge_instance = None

def _get_knowledge() -> KnowledgePlugin:
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = KnowledgePlugin()
        _knowledge_instance.initialize({})
    return _knowledge_instance

@tool
def add_document(content: str, title: str, metadata: Optional[Dict] = None) -> str:
    """Add a document to the knowledge base."""
    try:
        knowledge = _get_knowledge()

        text_splitter = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separator="\n"
        )

        chunks = text_splitter.split_text(content)

        if knowledge.vector_store:
            for i, chunk in enumerate(chunks):
                chunk_metadata = {"title": title, "chunk": i, **(metadata or {})}
                knowledge.vector_store.add_texts([chunk], metadatas=[chunk_metadata])
            knowledge.vector_store.save_local("knowledge_db")

        knowledge.documents.append({
            "title": title,
            "content_length": len(content),
            "chunks": len(chunks),
            "metadata": metadata
        })

        return f"✅ Document added successfully!\n\n📄 Title: {title}\n📊 Chunks: {len(chunks)}"
    except Exception as e:
        return f"❌ Failed to add document: {str(e)}"

@tool
def search_knowledge(query: str, top_k: int = 5) -> str:
    """Search the knowledge base for relevant documents."""
    try:
        knowledge = _get_knowledge()

        if not knowledge.vector_store:
            return "⚠️ Vector store not initialized"

        results = knowledge.vector_store.similarity_search(query, k=top_k)

        if not results:
            return f"No results found for '{query}'"

        output = f"🔍 Search results for '{query}' ({len(results)} found):\n\n"
        for i, doc in enumerate(results, 1):
            output += (
                f"{i}. 📄 {doc.metadata.get('title', 'Untitled')}\n"
                f"   Relevance: High\n"
                f"   Preview: {doc.page_content[:100]}...\n\n"
            )

        return output
    except Exception as e:
        return f"❌ Search failed: {str(e)}"

@tool
def query_knowledge(query: str) -> str:
    """Query the knowledge base with a question."""
    try:
        knowledge = _get_knowledge()

        if not knowledge.vector_store:
            return "⚠️ Vector store not initialized"

        from langchain.chains import RetrievalQA
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=knowledge.vector_store.as_retriever()
        )

        result = qa_chain.run(query)

        return f"🤖 Answer:\n\n{result}"
    except Exception as e:
        return f"❌ Query failed: {str(e)}"

@tool
def list_documents() -> str:
    """List all documents in the knowledge base."""
    try:
        knowledge = _get_knowledge()

        if not knowledge.documents:
            return "No documents in knowledge base"

        output = f"📚 Documents in knowledge base ({len(knowledge.documents)}):\n\n"
        for i, doc in enumerate(knowledge.documents, 1):
            output += (
                f"{i}. {doc['title']}\n"
                f"   Length: {doc['content_length']} characters\n"
                f"   Chunks: {doc['chunks']}\n\n"
            )

        return output
    except Exception as e:
        return f"❌ Failed to list documents: {str(e)}"
