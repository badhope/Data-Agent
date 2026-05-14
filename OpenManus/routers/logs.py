"""
日志管理API路由
提供日志文件的查看、搜索和管理功能
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from pydantic import BaseModel

from utils.log_manager import log_manager

router = APIRouter(prefix="/logs", tags=["日志管理"])


class LogStats(BaseModel):
    """日志统计信息"""
    total_files: int
    total_size: int
    by_type: dict
    recent_errors: int
    last_updated: Optional[str]


class LogFile(BaseModel):
    """日志文件信息"""
    name: str
    path: str
    size: int
    modified: str
    type: str


class LogEntry(BaseModel):
    """日志条目"""
    line: int
    time: str
    level: str
    source: str
    message: str
    file: Optional[str] = None


@router.get("/api/logs/stats")
async def get_log_stats():
    """获取日志统计信息"""
    try:
        stats = log_manager.get_log_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/logs/files")
async def get_log_files():
    """获取日志文件列表"""
    try:
        files = log_manager.get_log_files()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/logs/content")
async def get_log_content(
    filename: str = Query(..., description="日志文件名"),
    lines: int = Query(100, description="读取行数"),
    level: Optional[str] = Query(None, description="日志级别过滤")
):
    """读取日志文件内容"""
    try:
        entries = log_manager.read_log_content(filename, lines, level)
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/logs/search")
async def search_logs(
    keyword: str = Query(..., description="搜索关键词"),
    log_type: Optional[str] = Query(None, description="日志类型")
):
    """搜索日志内容"""
    try:
        results = log_manager.search_logs(keyword, log_type)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def logs_page():
    """日志查看器页面"""
    html_path = "templates/logs.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="日志页面未找到")
