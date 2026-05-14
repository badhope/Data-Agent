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
        """使用LLM生成结构化摘要"""
        from app.llm import LLM

        type_prompts = {
            "academic": """请对以下学术论文/文献内容生成结构化摘要，严格按JSON格式输出：
{
  "title": "论文标题",
  "summary": "核心摘要（200字以内）",
  "key_points": ["核心观点1", "核心观点2", "核心观点3"],
  "methodology": "研究方法概述",
  "conclusion": "主要结论",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}""",
            "meeting": """请对以下会议内容生成结构化摘要，严格按JSON格式输出：
{
  "title": "会议主题",
  "summary": "会议摘要（200字以内）",
  "key_points": ["要点1", "要点2"],
  "decisions": ["决议1", "决议2"],
  "action_items": ["行动项1", "行动项2"]
}""",
            "report": """请对以下报告内容生成结构化摘要，严格按JSON格式输出：
{
  "title": "报告标题",
  "summary": "报告摘要（200字以内）",
  "key_points": ["要点1", "要点2", "要点3"],
  "findings": ["发现1", "发现2"],
  "recommendations": ["建议1", "建议2"]
}""",
            "general": """请对以下内容生成结构化摘要，严格按JSON格式输出：
{
  "title": "文档标题",
  "summary": "内容摘要（200字以内）",
  "key_points": ["要点1", "要点2", "要点3"],
  "keywords": ["关键词1", "关键词2"]
}"""
        }

        prompt = type_prompts.get(document_type, type_prompts["general"])

        # 截断过长的文本
        max_input_length = 6000
        if len(text) > max_input_length:
            text = text[:max_input_length] + "\n\n[文档内容过长，已截断]"

        llm = LLM()
        messages = [
            {"role": "system", "content": prompt + "\n\n只输出JSON，不要输出其他内容。"},
            {"role": "user", "content": text}
        ]

        response = await llm.ask(messages)

        # 解析JSON结果
        import json
        import re
        # 尝试提取JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result
            except json.JSONDecodeError:
                pass

        # JSON解析失败时返回纯文本摘要
        return {
            "title": "",
            "summary": response,
            "key_points": [],
            "keywords": []
        }

    async def generate_meeting_minutes(
        self,
        text: str,
        meeting_date: Optional[str] = None,
        output_format: str = "dict"
    ) -> any:
        """使用LLM生成会议纪要"""
        from app.llm import LLM

        prompt = """请根据以下会议记录生成结构化的会议纪要。要求：
1. 提取会议主题
2. 总结各讨论要点（标注发言人）
3. 列出所有决议事项
4. 列出所有行动项（含负责人和截止时间）
5. 使用Markdown格式输出

输出格式：
# 会议纪要

## 会议信息
- 日期：[日期]
- 参会人员：[人员列表]

## 讨论要点
1. [要点1] - [发言人]
2. [要点2] - [发言人]

## 决议事项
1. [决议1]
2. [决议2]

## 行动项
| 任务 | 负责人 | 截止时间 |
|------|--------|---------|
| [任务1] | [负责人] | [截止时间] |"""

        date_str = f"\n会议日期：{meeting_date}" if meeting_date else ""

        llm = LLM()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"会议记录：{date_str}\n\n{text}"}
        ]

        response = await llm.ask(messages)

        if output_format == "markdown":
            return {"content": response, "format": "markdown"}
        else:
            return {"content": response, "format": "markdown"}

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
