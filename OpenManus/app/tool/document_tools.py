"""文档处理工具集"""
from typing import List, Dict, Optional
from app.tool.base import BaseTool, ToolResult
from app.services.document_service import DocumentService
from app.document.translator import MultiLanguageTranslator


class MeetingMinutesTool(BaseTool):
    """会议纪要生成工具"""
    
    name: str = "generate_meeting_minutes"
    description: str = "根据会议记录生成结构化的会议纪要，包括会议信息、讨论要点、决议事项和行动项"
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "会议记录文本内容"},
            "meeting_date": {"type": "string", "description": "会议日期（可选）"},
            "output_format": {"type": "string", "description": "输出格式：markdown 或 dict", "default": "markdown"}
        },
        "required": ["text"]
    }

    async def execute(self, text: str, meeting_date: Optional[str] = None, output_format: str = "markdown") -> ToolResult:
        """执行会议纪要生成"""
        try:
            service = DocumentService()
            result = await service.generate_meeting_minutes(text, meeting_date, output_format)
            return self.success_response(result)
        except Exception as e:
            return self.fail_response(f"生成会议纪要失败: {str(e)}")


class DocumentSummaryTool(BaseTool):
    """文档摘要工具"""
    
    name: str = "summarize_document"
    description: str = "对文档内容进行摘要处理，支持抽取式和生成式两种方式"
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "文档文本内容"},
            "method": {"type": "string", "description": "摘要方法：extractive（抽取式）或 abstractive（生成式）", "default": "extractive"},
            "max_length": {"type": "integer", "description": "最大摘要长度", "default": 200},
            "num_sentences": {"type": "integer", "description": "抽取句子数量", "default": 5},
            "document_type": {"type": "string", "description": "文档类型：general/academic/meeting/report/news", "default": "general"}
        },
        "required": ["text"]
    }

    async def execute(self, text: str, method: str = "extractive", max_length: int = 200, 
                     num_sentences: int = 5, document_type: str = "general") -> ToolResult:
        """执行文档摘要"""
        try:
            service = DocumentService()
            
            if document_type == "academic":
                result = await service.summarize_structured(text, "academic")
            elif document_type == "meeting":
                result = await service.summarize_structured(text, "meeting")
            elif document_type == "report":
                result = await service.summarize_structured(text, "report")
            else:
                result = await service.summarize_document(text, method, max_length, num_sentences)
            
            return self.success_response(result)
        except Exception as e:
            return self.fail_response(f"生成文档摘要失败: {str(e)}")


class TextTranslationTool(BaseTool):
    """多语言翻译工具"""
    
    name: str = "translate_text"
    description: str = "支持中英日韩等多语言翻译，保留格式，支持专业术语润色"
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "要翻译的文本"},
            "target_language": {"type": "string", "description": "目标语言代码：zh/en/ja/ko/fr/de/es/ru", "default": "en"},
            "source_language": {"type": "string", "description": "源语言代码（可选，自动检测）"},
            "quality": {"type": "string", "description": "翻译质量：standard/professional/premium", "default": "standard"},
            "preserve_formatting": {"type": "boolean", "description": "是否保留格式", "default": true}
        },
        "required": ["text", "target_language"]
    }

    async def execute(self, text: str, target_language: str, source_language: Optional[str] = None,
                     quality: str = "standard", preserve_formatting: bool = True) -> ToolResult:
        """执行翻译"""
        try:
            translator = MultiLanguageTranslator()
            result = translator.translate(text, target_language, source_language, quality, preserve_formatting)
            
            response = {
                "original_text": result.original_text,
                "translated_text": result.translated_text,
                "source_language": result.source_language,
                "target_language": result.target_language,
                "confidence": result.confidence,
                "word_count": result.word_count,
                "suggestions": result.suggestions
            }
            return self.success_response(response)
        except Exception as e:
            return self.fail_response(f"翻译失败: {str(e)}")


class TextPolishTool(BaseTool):
    """文本润色工具"""
    
    name: str = "polish_text"
    description: str = "文本润色工具，支持学术、正式、简洁、轻松等多种风格"
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "要润色的文本"},
            "style": {"type": "string", "description": "润色风格：academic（学术）/formal（正式）/casual（轻松）/concise（精简）", "default": "academic"},
            "language": {"type": "string", "description": "语言：zh/en/auto（自动检测）", "default": "auto"}
        },
        "required": ["text"]
    }

    async def execute(self, text: str, style: str = "academic", language: str = "auto") -> ToolResult:
        """执行文本润色"""
        try:
            service = DocumentService()
            result = await service.polish_text(text, style, language)
            return self.success_response(result)
        except Exception as e:
            return self.fail_response(f"文本润色失败: {str(e)}")


class PPTGenerationTool(BaseTool):
    """PPT生成工具"""
    
    name: str = "generate_ppt"
    description: str = "根据内容生成演示文稿，支持多种模板（商业报告、学术报告、会议纪要、项目提案、周报等）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "演示文稿标题"},
            "content": {"type": "object", "description": "各章节内容，键为章节名，值为要点列表"},
            "template": {"type": "string", "description": "模板类型：business/academic/meeting/proposal/weekly_report", "default": "business"}
        },
        "required": ["title", "content"]
    }

    async def execute(self, title: str, content: Dict[str, List[str]], template: str = "business") -> ToolResult:
        """执行PPT生成"""
        try:
            service = DocumentService()
            ppt_bytes = await service.generate_ppt_from_content(title, content, template)
            return ToolResult(output=f"PPT生成成功，共{len(content)}个章节", base64_image=None)
        except Exception as e:
            return self.fail_response(f"生成PPT失败: {str(e)}")


class TodoExtractTool(BaseTool):
    """待办事项提取工具"""
    
    name: str = "extract_todos"
    description: str = "从文本中提取待办事项，支持多语言识别"
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "包含待办事项的文本"}
        },
        "required": ["text"]
    }

    async def execute(self, text: str) -> ToolResult:
        """执行待办事项提取"""
        try:
            service = DocumentService()
            result = await service.extract_todos(text)
            return self.success_response(result)
        except Exception as e:
            return self.fail_response(f"提取待办事项失败: {str(e)}")


class OutlineGenerationTool(BaseTool):
    """文章提纲生成工具"""
    
    name: str = "generate_outline"
    description: str = "根据主题生成文章提纲，支持多种文档类型"
    parameters: dict = {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "文章主题"},
            "document_type": {"type": "string", "description": "文档类型：general/academic/report/meeting", "default": "general"},
            "depth": {"type": "integer", "description": "提纲深度（层级数）", "default": 3}
        },
        "required": ["topic"]
    }

    async def execute(self, topic: str, document_type: str = "general", depth: int = 3) -> ToolResult:
        """执行提纲生成"""
        try:
            service = DocumentService()
            result = await service.generate_outline_markdown(topic, document_type, depth)
            return self.success_response({"outline": result})
        except Exception as e:
            return self.fail_response(f"生成提纲失败: {str(e)}")


class ReportGenerationTool(BaseTool):
    """工作报告生成工具"""
    
    name: str = "generate_report"
    description: str = "根据工作项生成日报或周报"
    parameters: dict = {
        "type": "object",
        "properties": {
            "work_items": {"type": "array", "description": "工作项列表", "items": {"type": "object"}},
            "report_type": {"type": "string", "description": "报告类型：daily/weekly", "default": "weekly"},
            "author": {"type": "string", "description": "报告作者", "default": "DataAgent"}
        },
        "required": ["work_items"]
    }

    async def execute(self, work_items: List[Dict], report_type: str = "weekly", author: str = "DataAgent") -> ToolResult:
        """执行报告生成"""
        try:
            service = DocumentService()
            result = await service.generate_report(work_items, report_type, author)
            return self.success_response({"report": result})
        except Exception as e:
            return self.fail_response(f"生成报告失败: {str(e)}")


# 工具触发词映射
DOCUMENT_TOOL_TRIGGERS = {
    "generate_meeting_minutes": [
        "会议纪要", "会议记录", "会议总结", "meeting minutes", "meeting summary",
        "生成会议纪要", "整理会议记录", "会议内容总结"
    ],
    "summarize_document": [
        "摘要", "总结", "概括", "summary", "abstract",
        "生成摘要", "文献摘要", "论文摘要", "总结文档", "概括内容"
    ],
    "translate_text": [
        "翻译", "翻译文本", "translate", "翻译中文", "翻译英文",
        "英文翻译", "日语翻译", "韩语翻译", "多语言翻译"
    ],
    "polish_text": [
        "润色", "修改", "优化", "polish", "improve", "改写",
        "学术润色", "商务润色", "语言润色", "文本优化"
    ],
    "generate_ppt": [
        "PPT", "演示文稿", "幻灯片", "presentation",
        "生成PPT", "制作演示文稿", "创建幻灯片"
    ],
    "extract_todos": [
        "待办", "TODO", "任务列表", "待办事项", "提取任务", "todo list"
    ],
    "generate_outline": [
        "提纲", "大纲", "目录", "outline", "structure",
        "生成提纲", "文章结构", "论文大纲"
    ],
    "generate_report": [
        "报告", "周报", "日报", "工作总结", "work report",
        "生成周报", "生成日报", "工作总结报告"
    ]
}


def get_document_tools() -> List[BaseTool]:
    """获取所有文档处理工具"""
    return [
        MeetingMinutesTool(),
        DocumentSummaryTool(),
        TextTranslationTool(),
        TextPolishTool(),
        PPTGenerationTool(),
        TodoExtractTool(),
        OutlineGenerationTool(),
        ReportGenerationTool(),
    ]


def detect_tool_from_query(query: str) -> Optional[str]:
    """根据用户查询检测应该调用的工具"""
    query_lower = query.lower()
    
    for tool_name, triggers in DOCUMENT_TOOL_TRIGGERS.items():
        for trigger in triggers:
            if trigger.lower() in query_lower:
                return tool_name
    
    return None