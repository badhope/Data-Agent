"""
文档处理服务
整合所有文档处理功能
"""
from typing import List, Dict, Optional
from app.document.ppt_generator import PPTGenerator, PPTTemplate
from app.document.summarizer import DocumentSummarizer, StructuredSummaryGenerator
from app.document.meeting_minutes import MeetingMinutesGenerator, generate_meeting_minutes
from app.document.report_generator import ReportGenerator, generate_weekly_report, generate_daily_report
from app.document.formatter import format_chinese_text, format_document
from app.document.citation_manager import CitationManager, format_citation
from app.document.todo_extractor import TodoExtractor, extract_todos
from app.document.pdf_parser import PDFParser, parse_pdf_bytes, search_pdf_content
from app.document.outline_generator import OutlineGenerator, generate_outline, generate_outline_markdown


class DocumentService:
    """文档处理服务"""

    def __init__(self):
        self.ppt_generator = PPTGenerator()
        self.summarizer = DocumentSummarizer()
        self.summary_generator = StructuredSummaryGenerator()
        self.meeting_generator = MeetingMinutesGenerator()
        self.report_generator = ReportGenerator()
        self.citation_manager = CitationManager()
        self.todo_extractor = TodoExtractor()
        self.pdf_parser = PDFParser()
        self.outline_generator = OutlineGenerator()

    async def summarize_document(
        self,
        text: str,
        method: str = "extractive",
        max_length: int = 200,
        num_sentences: int = 5
    ) -> Dict:
        """生成文档摘要"""
        result = await self.summarizer.summarize(
            text=text,
            method=method,
            max_length=max_length,
            num_sentences=num_sentences
        )

        return {
            'original_length': result.original_length,
            'summary_length': result.summary_length,
            'compression_ratio': result.compression_ratio,
            'summary_type': result.summary_type,
            'full_summary': result.full_summary,
            'key_points': result.key_points,
            'keywords': result.keywords
        }

    async def summarize_structured(
        self,
        text: str,
        document_type: str = "general"
    ) -> Dict:
        """生成结构化摘要"""
        result = self.summary_generator.generate(text, document_type)
        return result

    async def generate_meeting_minutes(
        self,
        text: str,
        meeting_date: Optional[str] = None,
        output_format: str = "dict"
    ) -> any:
        """生成会议纪要"""
        return generate_meeting_minutes(text, meeting_date, output_format)

    async def generate_report(
        self,
        work_items: List[Dict],
        report_type: str = "weekly",
        author: str = "DataAgent"
    ) -> str:
        """生成工作报告"""
        # 转换参数格式：task -> title, description, 状态映射
        status_mapping = {
            '已完成': 'completed',
            '进行中': 'in_progress',
            '计划中': 'planned',
            'completed': 'completed',
            'in_progress': 'in_progress',
            'planned': 'planned'
        }
        
        converted_items = []
        for item in work_items:
            raw_status = item.get('status', 'completed')
            converted_item = {
                'title': item.get('task', item.get('title', '未命名任务')),
                'description': item.get('description', item.get('task', '')),
                'status': status_mapping.get(raw_status, 'completed'),
                'category': item.get('category', 'general'),
                'hours_spent': item.get('hours_spent'),
                'tags': item.get('tags', [])
            }
            converted_items.append(converted_item)

        if report_type == "weekly":
            return generate_weekly_report(converted_items, author)
        elif report_type == "daily":
            return generate_daily_report(converted_items, author)
        else:
            return generate_weekly_report(converted_items, author)

    async def extract_todos(self, text: str) -> Dict:
        """提取待办事项"""
        todos = self.todo_extractor.extract_from_text(text)
        return self.todo_extractor.to_dict(todos)

    async def format_text(
        self,
        text: str,
        format_level: str = "standard"
    ) -> Dict:
        """格式化文本"""
        return format_document(text, format_level)

    async def manage_citations(
        self,
        text: str = "",
        action: str = "format",
        citation_id: str = "",
        style: str = "gbt"
    ) -> any:
        """管理引用"""
        if action == "add":
            return self.citation_manager.add_from_text(text)

        elif action == "format":
            return self.citation_manager.format_bibliography(style)

        elif action == "get":
            if citation_id:
                return self.citation_manager.get_citation_by_id(citation_id)
            return None

        elif action == "list":
            return {
                'citations': [c.to_dict() for c in self.citation_manager.citations],
                'count': self.citation_manager.get_citation_count()
            }

        elif action == "export":
            return self.citation_manager.export_json()

        return None

    def get_ppt_templates(self) -> List[Dict]:
        """获取PPT模板列表"""
        return PPTTemplate.list_templates()

    async def generate_ppt_from_content(
        self,
        title: str,
        content: Dict[str, List[str]],
        template: str = "business"
    ) -> bytes:
        """根据内容生成PPT"""
        return PPTTemplate.generate_from_template(template, title, content)

    async def generate_meeting_ppt(
        self,
        meeting_text: str,
        meeting_date: Optional[str] = None
    ) -> bytes:
        """生成会议纪要PPT"""
        minutes = self.meeting_generator.generate_from_text(meeting_text, meeting_date)
        return self.meeting_generator.to_ppt(minutes)

    async def generate_report_ppt(
        self,
        work_items: List[Dict],
        report_type: str = "weekly"
    ) -> bytes:
        """生成工作报告PPT"""
        from app.document.report_generator import WorkItem

        items = [WorkItem(**item) for item in work_items]
        report = self.report_generator.generate(items, report_type)
        return self.report_generator.to_ppt(report)

    async def parse_pdf(
        self,
        pdf_bytes: bytes,
        extract_tables: bool = False
    ) -> Dict:
        """解析PDF文档"""
        try:
            return parse_pdf_bytes(pdf_bytes, extract_tables)
        except Exception as e:
            return {"error": str(e)}

    async def search_pdf(
        self,
        content: Dict,
        query: str
    ) -> List[Dict]:
        """在PDF内容中搜索"""
        return search_pdf_content(content, query)

    async def generate_outline(
        self,
        topic: str,
        document_type: str = "general",
        depth: int = 3
    ) -> Dict:
        """生成文章提纲"""
        return generate_outline(topic, document_type, depth)

    async def generate_outline_markdown(
        self,
        topic: str,
        document_type: str = "general",
        depth: int = 3
    ) -> str:
        """生成Markdown格式提纲"""
        return generate_outline_markdown(topic, document_type, depth)

    def get_outline_templates(self) -> List[Dict]:
        """获取提纲模板列表"""
        return self.outline_generator.get_templates()

    async def polish_text(
        self,
        text: str,
        style: str = "academic",
        language: str = "auto"
    ) -> Dict:
        """文本润色 - 学术与职场风格"""
        from app.llm import LLM

        # 定义不同风格的提示词
        style_prompts = {
            "academic": """请将以下文本润色为学术风格。要求：
1. 使用规范的学术用语和表达
2. 保持逻辑严谨，论证充分
3. 优化句式结构，避免口语化
4. 保持原意不变，提升专业性
5. 适当使用学术连接词（然而、因此、综上所述等）""",

            "casual": """请将以下文本改写为轻松自然的风格。要求：
1. 使用通俗易懂的语言
2. 适当使用口语化表达
3. 保持友好亲切的语气
4. 保持原意不变""",

            "formal": """请将以下文本改写为正式商务风格。要求：
1. 使用规范的商务用语
2. 语气专业、礼貌、简洁
3. 避免缩写和口语化表达
4. 适合职场正式场合""",

            "concise": """请将以下文本精简压缩。要求：
1. 删除冗余词汇和重复表达
2. 保留核心信息和关键观点
3. 使用简洁有力的句式
4. 保持原意不变"""
        }

        prompt = style_prompts.get(style, style_prompts["academic"])

        # 检测语言
        if language == "auto":
            # 简单检测：如果文本中中文字符占比高，则认为是中文
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            language = "zh" if chinese_chars / len(text) > 0.3 else "en"

        # 添加语言提示
        if language == "zh":
            prompt += "\n\n请用中文输出润色后的文本。"
        else:
            prompt += "\n\nPlease output the polished text in English."

        llm = LLM()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请润色以下文本：\n\n{text}"}
        ]

        response = await llm.ask(messages)
        polished_text = response

        return {
            "original_text": text,
            "polished_text": polished_text,
            "style": style,
            "language": language,
            "original_length": len(text),
            "polished_length": len(polished_text)
        }
