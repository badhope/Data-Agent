"""
API Module
"""
from fastapi import APIRouter
from web.api.v1 import (
    knowledge_router,
    skills_router,
    mcp_router,
    chat_router,
    settings_router,
    analytics_router
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(skills_router)
api_router.include_router(mcp_router)
api_router.include_router(settings_router)
api_router.include_router(analytics_router)
