from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .sandbox import execute_code, get_supported_languages

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


class SandboxRequest(BaseModel):
    code: str
    language: str = "python"
    session_id: Optional[str] = None


class SandboxResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    images: List[str] = []
    duration_ms: int
    language: str


@router.post("/execute", response_model=SandboxResponse)
async def sandbox_execute(request: SandboxRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="代码不能为空")
    if len(request.code) > 50000:
        raise HTTPException(status_code=400, detail="代码长度不能超过50000字符")
    result = execute_code(
        code=request.code,
        language=request.language,
        session_id=request.session_id,
    )
    result["language"] = request.language
    return SandboxResponse(**result)


@router.get("/languages")
async def sandbox_languages():
    return {"languages": get_supported_languages()}
