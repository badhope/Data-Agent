"""
API V1 Module
"""
from .knowledge import router as knowledge_router
from .skills import router as skills_router
from .mcp import router as mcp_router
from .chat import router as chat_router
from .settings import router as settings_router
from .analytics import router as analytics_router

__all__ = [
    "knowledge_router",
    "skills_router",
    "mcp_router",
    "chat_router",
    "settings_router",
    "analytics_router"
]
