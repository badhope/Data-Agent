"""
Dependencies for API
"""
from fastapi import Depends, HTTPException, status
from typing import Optional

async def get_current_user():
    """获取当前用户 - 临时实现"""
    # TODO: 实现真实的用户认证
    return {"id": "default_user", "name": "Default User"}
