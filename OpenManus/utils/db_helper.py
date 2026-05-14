"""数据库查询辅助函数"""
import sqlite3
import logging
from contextlib import contextmanager
from fastapi import HTTPException
from database import databases

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection(db_id: str):
    """获取数据库连接的上下文管理器，确保连接正确关闭"""
    if db_id not in databases:
        raise HTTPException(status_code=404, detail="数据库不存在")
    db = databases[db_id]
    conn = sqlite3.connect(db.path)
    try:
        yield conn
    finally:
        conn.close()

def get_kb_or_404(kb_id: str):
    """获取知识库或返回404"""
    from database import knowledge_bases
    if kb_id not in knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return knowledge_bases[kb_id]

def get_mcp_or_404(server_id: str):
    """获取MCP服务器或返回404"""
    from database import mcp_servers
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    return mcp_servers[server_id]

def get_conversation_or_404(conv_id: str):
    """获取对话或返回404"""
    from database import conversations
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversations[conv_id]
