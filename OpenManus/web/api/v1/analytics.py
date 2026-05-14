"""
Analytics API Router - Financial Analysis & Data Processing
Integrating competition features
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.post("/query")
async def analytics_query(request: Dict[str, Any]):
    """数据分析查询 - 自然语言转SQL"""
    try:
        from web.tidycup.nl2sql_engine import FullNL2SQLPipeline
        
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        db_path = Path(__file__).parent.parent.parent.parent / "data" / "analytics.db"
        pipeline = FullNL2SQLPipeline(db_path)
        pipeline.initialize()
        
        result = await pipeline.process_query(query)
        
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/pdf")
async def upload_pdf_for_analysis(file: UploadFile = File(...)):
    """上传PDF进行智能解析"""
    try:
        from web.tidycup.pdf_parser import DualEnginePDFParser
        
        # 保存上传的文件
        data_dir = Path(__file__).parent.parent.parent.parent / "data" / "uploads"
        data_dir.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        file_path = data_dir / f"{file_id}_{file.filename}"
        
        import shutil
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        parser = DualEnginePDFParser()
        result = await parser.parse(str(file_path))
        
        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "result": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_analytics_status():
    """获取分析系统状态"""
    return JSONResponse({
        "available": True,
        "features": [
            "pdf_parsing",
            "nl2sql",
            "rag",
            "multi_intent_planning",
            "attribution_analysis"
        ]
    })
