"""
DataAgent - 服务层模块
统一导出所有服务函数，供路由层调用
"""

from services.llm_service import call_llm, call_llm_with_system, call_llm_json, execute_python, test_connection
from services.embedding_service import generate_embeddings, cosine_similarity, batch_generate_embeddings
from services.knowledge_service import clean_text, process_document, split_into_chunks, search_knowledge_base
from services.mcp_service import execute_mcp_command, test_mcp_connection, list_mcp_tools, list_mcp_resources

__all__ = [
    # LLM 服务
    "call_llm",
    "call_llm_with_system",
    "call_llm_json",
    "execute_python",
    "test_connection",
    # 嵌入服务
    "generate_embeddings",
    "cosine_similarity",
    "batch_generate_embeddings",
    # 知识库服务
    "clean_text",
    "process_document",
    "split_into_chunks",
    "search_knowledge_base",
    # MCP 服务
    "execute_mcp_command",
    "test_mcp_connection",
    "list_mcp_tools",
    "list_mcp_resources",
]
