"""
DataAgent - 全局异常处理中间件
统一的错误处理、日志记录和响应格式化
"""

import traceback
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)

            # 记录请求日志
            duration = time.time() - start_time
            status_code = response.status_code

            if status_code >= 500:
                print(f"[ERROR] {request.method} {request.url.path} -> {status_code} ({duration:.2f}s)")
            elif status_code >= 400:
                print(f"[WARN] {request.method} {request.url.path} -> {status_code} ({duration:.2f}s)")

            return response

        except Exception as e:
            duration = time.time() - start_time
            print(f"[CRITICAL] {request.method} {request.url.path} -> UNHANDLED ({duration:.2f}s)")
            print(f"[CRITICAL] Error: {str(e)}")
            print(f"[CRITICAL] Traceback: {traceback.format_exc()}")

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "服务器内部错误",
                    "detail": str(e)[:200] if len(str(e)) > 200 else str(e)
                }
            )
