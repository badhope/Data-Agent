"""
DataAgent - 路由模块
将所有 API 路由按功能拆分为独立模块
"""

from routers.settings import router as settings_router
from routers.knowledge import router as knowledge_router
from routers.skills import router as skills_router
from routers.mcp import router as mcp_router
from routers.conversations import router as conversations_router
from routers.databases import router as databases_router
from routers.financial import router as financial_router
from routers.nl2sql import router as nl2sql_router
from routers.visualization import router as visualization_router
from routers.agent import router as agent_router

__all__ = [
    "settings_router",
    "knowledge_router",
    "skills_router",
    "mcp_router",
    "conversations_router",
    "databases_router",
    "financial_router",
    "nl2sql_router",
    "visualization_router",
    "agent_router",
]
