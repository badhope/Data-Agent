"""
DataAgent - 简易速率限制器
基于内存的滑动窗口速率限制
"""

import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于IP的速率限制中间件"""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"

        # WebSocket 不限制
        if request.url.path == "/ws":
            return await call_next(request)

        # 静态文件不限制
        if request.url.path.startswith("/static"):
            return await call_next(request)

        now = time.time()

        # 清理过期记录
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]

        # 检查是否超限
        if len(self.requests[client_ip]) >= self.max_requests:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "请求过于频繁，请稍后再试"}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
