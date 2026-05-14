"""
PPT生成模块
基于python-pptx的演示文稿生成功能
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from typing import List, Dict, Optional
import io
from datetime import datetime


class PPTGenerator:
    """基于python-pptx的PPT生成器"""

    def __init__(self):
        self.presentation = None
        self.current_slide = None
        self._setup_chinese_support()

    def _setup_chinese_support(self):
        """设置中文支持"""
        from pptx.oxml.xmlchemy import OxmlElement
        
        def set_element_text(element, text):
            """设置元素文本，支持中文"""
            if text:
                element.text = text
        
        self._set_text = set_element_text

    def create_presentation(self, title: str = "演示文稿", author: str = "DataAgent"):
        """创建新演示文稿"""
        self.presentation = Presentation()
        # 使用英文避免编码问题
        self.presentation.core_properties.author = "DataAgent" if author else "DataAgent"
        self.presentation.core_properties.title = "Presentation" if title else "Presentation"
        self.presentation.core_properties.created = datetime.now()

    def add_title_slide(self, title: str, subtitle: str = ""):
        """添加标题页"""
        slide_layout = self.presentation.slide_layouts[0]
        slide = self.presentation.slides.add_slide(slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = title

        if subtitle:
            subtitle_shape = slide.placeholders[1]
            subtitle_shape.text = subtitle

        self.current_slide = slide
        return slide

    def add_content_slide(self, title: str, content: List[str],
                          layout_index: int = 1):
        """添加内容页"""
        slide_layout = self.presentation.slide_layouts[layout_index]
        slide = self.presentation.slides.add_slide(slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = title

        if len(slide.placeholders) > 1:
            body_shape = slide.placeholders[1]
            text_frame = body_shape.text_frame
            text_frame.clear()

            for i, point in enumerate(content):
                if i == 0:
                    p = text_frame.paragraphs[0]
                else:
                    p = text_frame.add_paragraph()

                p.text = "• " + point if not point.startswith(('•', '-', '1.', '2.')) else point
                p.level = 0

        self.current_slide = slide
        return slide

    def add_two_column_slide(self, title: str, left_content: List[str],
                            right_content: List[str]):
        """添加双栏内容页"""
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = title

        left_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5),
                                          Inches(4.25), Inches(5))
        left_frame = left_box.text_frame
        left_frame.word_wrap = True

        for i, point in enumerate(left_content):
            if i == 0:
                p = left_frame.paragraphs[0]
            else:
                p = left_frame.add_paragraph()
            p.text = "• " + point if not point.startswith(('•', '-')) else point

        right_box = slide.shapes.add_textbox(Inches(5), Inches(1.5),
                                           Inches(4.25), Inches(5))
        right_frame = right_box.text_frame
        right_frame.word_wrap = True

        for i, point in enumerate(right_content):
            if i == 0:
                p = right_frame.paragraphs[0]
            else:
                p = right_frame.add_paragraph()
            p.text = "• " + point if not point.startswith(('•', '-')) else point

        self.current_slide = slide
        return slide

    def add_image_slide(self, title: str, image_path: str = None,
                       description: str = ""):
        """添加图片页"""
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = title

        if image_path:
            try:
                slide.shapes.add_picture(
                    image_path,
                    Inches(1),
                    Inches(2),
                    width=Inches(8)
                )
            except Exception as e:
                pass

        if description:
            desc_box = slide.shapes.add_textbox(
                Inches(1),
                Inches(6),
                Inches(8),
                Inches(1)
            )
            desc_frame = desc_box.text_frame
            p = desc_frame.paragraphs[0]
            p.text = description
            p.alignment = PP_ALIGN.CENTER

        self.current_slide = slide
        return slide

    def add_table_slide(self, title: str, headers: List[str],
                       rows: List[List[str]]):
        """添加表格页"""
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = title

        rows_count = len(rows) + 1
        cols_count = len(headers)

        table = slide.shapes.add_table(
            rows_count,
            cols_count,
            Inches(0.5),
            Inches(1.8),
            Inches(9),
            Inches(0.5 * rows_count)
        ).table

        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.fill.solid()
            from pptx.dml.color import RGBColor
            cell.fill.fore_color.rgb = RGBColor(0, 51, 102)

        for row_idx, row_data in enumerate(rows):
            for col_idx, cell_text in enumerate(row_data):
                cell = table.cell(row_idx + 1, col_idx)
                cell.text = str(cell_text)

        self.current_slide = slide
        return slide

    def add_section_slide(self, section_title: str):
        """添加章节分隔页"""
        slide_layout = self.presentation.slide_layouts[2]
        slide = self.presentation.slides.add_slide(slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = section_title

        self.current_slide = slide
        return slide

    def add_blank_slide(self):
        """添加空白页"""
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)
        self.current_slide = slide
        return slide

    def set_slide_background(self, color: tuple = (255, 255, 255)):
        """设置幻灯片背景颜色"""
        if self.current_slide:
            background = self.current_slide.background
            fill = background.fill
            fill.solid()
            from pptx.dml.color import RGBColor
            fill.fore_color.rgb = RGBColor(*color)

    def save(self, output_path: str):
        """保存演示文稿"""
        if self.presentation:
            import io
            if isinstance(output_path, io.BytesIO):
                self.presentation.save(output_path)
            else:
                self.presentation.save(output_path)
            return True
        return False

    def save_to_bytes(self) -> bytes:
        """保存演示文稿为字节流"""
        import io
        output = io.BytesIO()
        if self.presentation:
            try:
                self.presentation.save(output)
                return output.getvalue()
            except Exception as e:
                import logging
                logging.error(f"PPT save error: {e}")
                return b''
        return b''

    def get_bytes(self) -> bytes:
        """获取二进制内容"""
        if not self.presentation:
            return b""

        import io
        buffer = io.BytesIO()
        try:
            # 确保所有文本都是字符串类型
            self._sanitize_text()
            self.presentation.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            import logging
            logging.error(f"PPT get_bytes error: {e}")
            return b""

    def _sanitize_text(self):
        """清理所有幻灯片中的文本，确保编码正确"""
        if not self.presentation:
            return
        
        for slide in self.presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text_frame"):
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if run.text:
                                # 确保文本是字符串
                                run.text = str(run.text)
                elif hasattr(shape, "text"):
                    if shape.text:
                        shape.text = str(shape.text)

    def get_slide_count(self) -> int:
        """获取幻灯片数量"""
        return len(self.presentation.slides) if self.presentation else 0


class PPTTemplate:
    """PPT模板管理器"""

    TEMPLATES = {
        "business": {
            "name": "商业报告",
            "description": "专业的商业分析报告模板",
            "slides": ["封面", "目录", "概述", "数据分析", "结论建议"],
            "color_scheme": {
                "primary": (0, 51, 102),
                "secondary": (0, 102, 153),
                "accent": (255, 153, 0)
            }
        },
        "academic": {
            "name": "学术报告",
            "description": "学术研究演示模板",
            "slides": ["标题", "研究背景", "方法", "结果", "讨论", "结论"],
            "color_scheme": {
                "primary": (51, 51, 51),
                "secondary": (102, 102, 102),
                "accent": (0, 102, 204)
            }
        },
        "meeting": {
            "name": "会议纪要",
            "description": "简洁的会议演示模板",
            "slides": ["会议主题", "议程", "讨论要点", "行动计划", "下次会议"],
            "color_scheme": {
                "primary": (51, 51, 51),
                "secondary": (102, 102, 102),
                "accent": (204, 0, 0)
            }
        },
        "proposal": {
            "name": "项目提案",
            "description": "项目方案展示模板",
            "slides": ["项目概述", "目标", "方案", "时间表", "预算", "风险评估"],
            "color_scheme": {
                "primary": (0, 102, 102),
                "secondary": (0, 153, 153),
                "accent": (255, 153, 0)
            }
        },
        "weekly_report": {
            "name": "周报",
            "description": "工作周报模板",
            "slides": ["本周总结", "本周完成", "本周进展", "下周计划", "问题与建议"],
            "color_scheme": {
                "primary": (0, 102, 51),
                "secondary": (0, 153, 76),
                "accent": (255, 153, 0)
            }
        }
    }

    @classmethod
    def get_template(cls, template_id: str) -> Dict:
        """获取模板配置"""
        return cls.TEMPLATES.get(template_id, cls.TEMPLATES["business"])

    @classmethod
    def list_templates(cls) -> List[Dict]:
        """列出所有模板"""
        return [
            {"id": key, **value}
            for key, value in cls.TEMPLATES.items()
        ]

    @classmethod
    def generate_from_template(
        cls,
        template_id: str,
        title: str,
        content: Dict[str, List[str]]
    ) -> bytes:
        """使用模板生成PPT"""
        template = cls.get_template(template_id)
        generator = PPTGenerator()
        generator.create_presentation(title)

        generator.add_title_slide(title, template["name"])

        for section_title in template["slides"][1:]:
            section_key = section_title.replace(" ", "_").lower()
            section_content = content.get(section_key, [])

            if section_content:
                generator.add_content_slide(section_title, section_content)

        return generator.get_bytes()
