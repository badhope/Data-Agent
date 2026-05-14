"""
文档处理API路由
提供文档生成、摘要、格式化等API
"""
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.document_service import DocumentService
import io

router = APIRouter(prefix="/documents", tags=["文档处理"])
doc_service = DocumentService()


class SummarizeRequest(BaseModel):
    text: str
    method: str = "extractive"
    max_length: int = 200
    num_sentences: int = 5


class StructuredSummaryRequest(BaseModel):
    text: str
    document_type: str = "general"


class MeetingMinutesRequest(BaseModel):
    text: str
    meeting_date: Optional[str] = None
    output_format: str = "markdown"


class ReportRequest(BaseModel):
    work_items: List[Dict]
    report_type: str = "weekly"
    author: str = "DataAgent"


class TodoExtractRequest(BaseModel):
    text: str


class FormatRequest(BaseModel):
    text: str
    format_level: str = "standard"


class PPTContentRequest(BaseModel):
    title: str
    content: Dict[str, List[str]]
    template: str = "business"


class MeetingPPtRequest(BaseModel):
    text: str
    meeting_date: Optional[str] = None


class CitationRequest(BaseModel):
    text: str = ""
    action: str = "format"
    citation_id: str = ""
    style: str = "gbt"


class PolishRequest(BaseModel):
    text: str
    style: str = "academic"  # academic, casual, formal, concise
    language: str = "auto"   # auto, zh, en


@router.post("/summarize")
async def summarize_document(request: SummarizeRequest):
    """生成文档摘要"""
    try:
        result = await doc_service.summarize_document(
            text=request.text,
            method=request.method,
            max_length=request.max_length,
            num_sentences=request.num_sentences
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize/structured")
async def summarize_structured(request: StructuredSummaryRequest):
    """生成结构化摘要"""
    try:
        result = await doc_service.summarize_structured(
            text=request.text,
            document_type=request.document_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting-minutes")
async def generate_meeting_minutes(request: MeetingMinutesRequest):
    """生成会议纪要"""
    try:
        result = await doc_service.generate_meeting_minutes(
            text=request.text,
            meeting_date=request.meeting_date,
            output_format=request.output_format
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meeting-minutes/ppt")
async def generate_meeting_minutes_ppt(request: MeetingPPtRequest):
    """生成会议纪要PPT"""
    try:
        ppt_bytes = await doc_service.generate_meeting_ppt(
            meeting_text=request.text,
            meeting_date=request.meeting_date
        )

        return StreamingResponse(
            iter([ppt_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": "attachment; filename=meeting_minutes.pptx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def generate_report(request: ReportRequest):
    """生成工作报告"""
    try:
        result = await doc_service.generate_report(
            work_items=request.work_items,
            report_type=request.report_type,
            author=request.author
        )
        return {"report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report/ppt")
async def generate_report_ppt(request: ReportRequest):
    """生成工作报告PPT"""
    try:
        ppt_bytes = await doc_service.generate_report_ppt(
            work_items=request.work_items,
            report_type=request.report_type
        )

        return StreamingResponse(
            iter([ppt_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename={request.report_type}_report.pptx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todos")
async def extract_todos(request: TodoExtractRequest):
    """提取待办事项"""
    try:
        result = await doc_service.extract_todos(text=request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/format")
async def format_text(request: FormatRequest):
    """格式化文本"""
    try:
        result = await doc_service.format_text(
            text=request.text,
            format_level=request.format_level
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ppt/templates")
async def get_ppt_templates():
    """获取PPT模板列表"""
    try:
        templates = doc_service.get_ppt_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ppt/generate")
async def generate_ppt(request: PPTContentRequest):
    """生成PPT"""
    try:
        ppt_bytes = await doc_service.generate_ppt_from_content(
            title=request.title,
            content=request.content,
            template=request.template
        )

        return StreamingResponse(
            iter([ppt_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename={request.title}.pptx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/citations")
async def manage_citations(request: CitationRequest):
    """管理引用"""
    try:
        result = await doc_service.manage_citations(
            text=request.text,
            action=request.action,
            citation_id=request.citation_id,
            style=request.style
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PDFSearchRequest(BaseModel):
    content: Dict
    query: str


class OutlineRequest(BaseModel):
    topic: str
    document_type: str = "general"
    depth: int = 3


@router.post("/pdf/parse")
async def parse_pdf(file: UploadFile = File(...), extract_tables: bool = False):
    """解析PDF文档"""
    try:
        pdf_bytes = await file.read()
        result = await doc_service.parse_pdf(pdf_bytes, extract_tables)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf/search")
async def search_pdf(request: PDFSearchRequest):
    """在PDF内容中搜索"""
    try:
        result = await doc_service.search_pdf(request.content, request.query)
        return {"results": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outline")
async def generate_outline(request: OutlineRequest):
    """生成文章提纲"""
    try:
        result = await doc_service.generate_outline(
            topic=request.topic,
            document_type=request.document_type,
            depth=request.depth
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outline/markdown")
async def generate_outline_markdown(request: OutlineRequest):
    """生成Markdown格式提纲"""
    try:
        result = await doc_service.generate_outline_markdown(
            topic=request.topic,
            document_type=request.document_type,
            depth=request.depth
        )
        return {"markdown": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outline/templates")
async def get_outline_templates():
    """获取提纲模板列表"""
    try:
        templates = doc_service.get_outline_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polish")
async def polish_text(request: PolishRequest):
    """文本润色 - 学术与职场风格"""
    try:
        result = await doc_service.polish_text(
            text=request.text,
            style=request.style,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def documents_index():
    """文档处理API首页"""
    return {
        "message": "DataAgent 文档处理 API",
        "endpoints": {
            "POST /documents/summarize": "生成文档摘要",
            "POST /documents/summarize/structured": "生成结构化摘要",
            "POST /documents/meeting-minutes": "生成会议纪要",
            "POST /documents/meeting-minutes/ppt": "生成会议纪要PPT",
            "POST /documents/report": "生成工作报告",
            "POST /documents/report/ppt": "生成工作报告PPT",
            "POST /documents/todos": "提取待办事项",
            "POST /documents/format": "格式化文本",
            "POST /documents/polish": "文本润色（学术/职场风格）",
            "GET /documents/ppt/templates": "获取PPT模板",
            "POST /documents/ppt/generate": "生成PPT",
            "POST /documents/citations": "管理引用",
            "POST /documents/pdf/parse": "解析PDF文档",
            "POST /documents/pdf/search": "在PDF中搜索",
            "POST /documents/outline": "生成文章提纲",
            "POST /documents/outline/markdown": "生成Markdown格式提纲",
            "GET /documents/outline/templates": "获取提纲模板列表",
        }
    }
