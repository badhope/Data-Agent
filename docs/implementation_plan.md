# DataAgent 功能扩展实现计划

> **目标：** 在现有OpenManus框架中集成文档处理、内容生成等核心功能

**核心策略：** 基于现有开源项目进行模块化集成和修改

---

## 📋 参考的开源项目

### 1. PPT生成相关
- **python-pptx** (https://github.com/scanny/python-pptx) - 最流行的Python PPT库
- **odin-slides** (https://github.com/leonid20000/odin-slides) - 基于LLM的PPT生成 (146 stars)
- **Deckster** (https://github.com/jaredkirby/deckster) - JSON数据驱动PPT生成

### 2. 会议纪要相关
- **meeting-minutes** (https://github.com/NickMezacapa/meeting-minutes) - Whisper + GPT-4会议纪要
- **meeting-transcriber** (https://github.com/jfcostello/meeting-transcriber) - 会议转录摘要 (19 stars)

### 3. 工作报告相关
- **SmartBrief** (https://github.com/Estelle925/SmartBrief) - AI智能工作报告 (132 stars)
- **git-reporter-ai** - Git提交分析报告生成

### 4. 文档摘要相关
- **Text-Summarization-Models** (https://github.com/Tuhin-SnapD/Text-Summarization-Models) - 31种摘要模型
- **cjk-text-formatter** (https://github.com/xiaolai/cjk-text-formatter) - CJK文本格式化 (33 stars)

---

## 🎯 实现优先级

### 第一阶段：核心文档处理（必须实现）
1. ✅ **PPT生成模块** - 基于python-pptx + odin-slides
2. ✅ **文档摘要模块** - 集成Text-Summarization-Models
3. ✅ **会议纪要生成** - 基于现有文本处理能力
4. ✅ **周报/工作汇报生成** - 模板 + AI生成

### 第二阶段：内容优化（重要）
5. ⏳ **自动排版模块** - 基于cjk-text-formatter
6. ⏳ **文风优化/学术润色** - 提示词工程
7. ⏳ **引用整理** - 参考文献格式化
8. ⏳ **待办提取** - 任务识别

### 第三阶段：高级功能（扩展）
9. ⏳ **多Agent协同** - 任务调度优化
10. ⏳ **溯源链路面板** - 可视化增强

---

## 📁 目录结构设计

```
OpenManus/
├── app/
│   ├── document/                    # 文档处理模块
│   │   ├── __init__.py
│   │   ├── pdf_parser.py           # PDF解析（已有）
│   │   ├── ppt_generator.py         # PPT生成 ⭐
│   │   ├── summarizer.py            # 文档摘要 ⭐
│   │   ├── meeting_minutes.py        # 会议纪要 ⭐
│   │   ├── report_generator.py       # 周报/工作汇报 ⭐
│   │   ├── formatter.py              # 自动排版 ⭐
│   │   ├── citation_manager.py       # 引用整理 ⭐
│   │   └── task_extractor.py         # 待办提取 ⭐
│   │
│   └── services/
│       ├── document_service.py       # 文档处理服务
│       └── content_service.py        # 内容生成服务
│
├── routers/
│   ├── documents.py                 # 文档处理API ⭐
│   └── content.py                    # 内容生成API ⭐
│
└── static/
    └── templates/
        └── report_templates/         # 报告模板
            ├── weekly_report.md
            ├── meeting_summary.md
            └── business_report.md
```

---

## 🚀 详细实现任务

### 任务1：PPT生成模块

**文件：**
- 创建：`app/document/ppt_generator.py`
- 修改：`app/tool/__init__.py`
- 添加配置：`config/schema/ppt_schema.json`

**实现步骤：**

- [ ] **Step 1: 创建PPT生成核心类**

```python
# app/document/ppt_generator.py
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor
from pptx.enum.text import PP_ALIGN
from typing import List, Dict, Optional
import io

class PPTGenerator:
    """基于python-pptx的PPT生成器"""

    def __init__(self):
        self.presentation = None
        self.slide_layouts = None

    def create_presentation(self, title: str, author: str = "DataAgent"):
        """创建新演示文稿"""
        self.presentation = Presentation()
        self.presentation.core_properties.author = author
        self.presentation.core_properties.title = title

    def add_title_slide(self, title: str, subtitle: str = ""):
        """添加标题页"""
        slide_layout = self.presentation.slide_layouts[0]  # 标题页布局
        slide = self.presentation.slides.add_slide(slide_layout)

        # 设置标题
        title_shape = slide.shapes.title
        title_shape.text = title

        # 设置副标题
        subtitle_shape = slide.placeholders[1]
        subtitle_shape.text = subtitle

    def add_content_slide(self, title: str, content: List[str],
                         layout_type: str = "bullet"):
        """添加内容页"""
        slide_layout = self.presentation.slide_layouts[1]  # 内容页布局
        slide = self.presentation.slides.add_slide(slide_layout)

        # 设置标题
        title_shape = slide.shapes.title
        title_shape.text = title

        # 添加内容
        body_shape = slide.placeholders[1]
        text_frame = body_shape.text_frame
        text_frame.clear()

        for i, point in enumerate(content):
            if i == 0:
                p = text_frame.paragraphs[0]
            else:
                p = text_frame.add_paragraph()

            p.text = point
            p.level = 0

    def add_chart_slide(self, title: str, chart_data: Dict):
        """添加图表页"""
        slide_layout = self.presentation.slide_layouts[5]  # 空白布局
        slide = self.presentation.slides.add_slide(slide_layout)

        # 添加标题
        left = Inches(0.5)
        top = Inches(0.3)
        width = Inches(9)
        height = Inches(0.8)

        title_box = slide.shapes.add_textbox(left, top, width, height)
        text_frame = title_box.text_frame
        p = text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(32)
        p.font.bold = True

        # 添加图表占位（实际图表由数据决定）

    def save(self, output_path: str):
        """保存演示文稿"""
        self.presentation.save(output_path)

    def get_bytes(self) -> bytes:
        """获取二进制内容"""
        buffer = io.BytesIO()
        self.presentation.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
```

- [ ] **Step 2: 创建模板管理器**

```python
# app/document/ppt_templates.py
from typing import Dict, List

class PPTTemplate:
    """PPT模板定义"""

    TEMPLATES = {
        "business": {
            "name": "商业报告",
            "slides": ["封面", "目录", "概述", "数据分析", "结论建议"],
            "color_scheme": {
                "primary": (0, 51, 102),    # 深蓝色
                "secondary": (0, 102, 153), # 蓝色
                "accent": (255, 153, 0)     # 橙色
            }
        },
        "academic": {
            "name": "学术报告",
            "slides": ["标题", "研究背景", "方法", "结果", "讨论", "结论"],
            "color_scheme": {
                "primary": (51, 51, 51),
                "secondary": (102, 102, 102),
                "accent": (0, 102, 204)
            }
        },
        "meeting": {
            "name": "会议纪要",
            "slides": ["会议主题", "议程", "讨论要点", "行动计划", "下次会议"],
            "color_scheme": {
                "primary": (51, 51, 51),
                "secondary": (102, 102, 102),
                "accent": (204, 0, 0)
            }
        },
        "proposal": {
            "name": "项目提案",
            "slides": ["项目概述", "目标", "方案", "时间表", "预算", "风险评估"],
            "color_scheme": {
                "primary": (0, 102, 102),
                "secondary": (0, 153, 153),
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
```

- [ ] **Step 3: 创建PPT生成服务**

```python
# app/services/ppt_service.py
from app.document.ppt_generator import PPTGenerator
from app.document.ppt_templates import PPTTemplate
from typing import Dict, List, Optional
import asyncio

class PPTService:
    """PPT生成服务"""

    def __init__(self):
        self.generator = PPTGenerator()

    async def generate_from_content(
        self,
        title: str,
        content: Dict[str, List[str]],
        template: str = "business"
    ) -> bytes:
        """根据内容生成PPT"""
        template_config = PPTTemplate.get_template(template)

        self.generator.create_presentation(title)

        # 添加标题页
        self.generator.add_title_slide(
            title,
            f"由 DataAgent 生成 | {template_config['name']}"
        )

        # 根据内容类型生成幻灯片
        for slide_title, slide_content in content.items():
            if isinstance(slide_content, list):
                self.generator.add_content_slide(slide_title, slide_content)
            elif isinstance(slide_content, dict):
                # 图表数据
                self.generator.add_chart_slide(slide_title, slide_content)

        return self.generator.get_bytes()

    async def generate_meeting_minutes(
        self,
        meeting_info: Dict,
        discussion_points: List[Dict],
        action_items: List[Dict]
    ) -> bytes:
        """生成会议纪要PPT"""
        self.generator.create_presentation(
            f"会议纪要 - {meeting_info.get('title', '会议')}"
        )

        # 封面
        self.generator.add_title_slide(
            meeting_info.get('title', '会议纪要'),
            f"时间：{meeting_info.get('date', '未知')}\n"
            f"主持人：{meeting_info.get('host', '未知')}"
        )

        # 议程
        self.generator.add_content_slide(
            "会议议程",
            meeting_info.get('agenda', [])
        )

        # 讨论要点
        for point in discussion_points:
            self.generator.add_content_slide(
                point.get('title', '讨论点'),
                point.get('content', [])
            )

        # 行动计划
        action_text = [
            f"• {item.get('task', '')} - {item.get('assignee', '')} - {item.get('deadline', '')}"
            for item in action_items
        ]
        self.generator.add_content_slide("行动计划", action_text)

        return self.generator.get_bytes()
```

- [ ] **Step 4: 添加API路由**

```python
# routers/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.services.ppt_service import PPTService
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/documents", tags=["文档处理"])
ppt_service = PPTService()

class PPTRequest(BaseModel):
    title: str
    content: Dict[str, List[str]]
    template: str = "business"

@router.post("/ppt/generate")
async def generate_ppt(request: PPTRequest):
    """生成PPT"""
    try:
        ppt_bytes = await ppt_service.generate_from_content(
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

@router.get("/ppt/templates")
async def list_templates():
    """获取PPT模板列表"""
    from app.document.ppt_templates import PPTTemplate
    return PPTTemplate.list_templates()
```

- [ ] **Step 5: 更新requirements.txt**

```txt
# 添加到 requirements.txt
python-pptx>=0.6.21
```

- [ ] **Step 6: 测试**

```bash
# 测试PPT生成
cd /workspace/OpenManus
python -c "
from app.document.ppt_generator import PPTGenerator
from app.document.ppt_templates import PPTTemplate

# 测试生成
gen = PPTGenerator()
gen.create_presentation('测试报告')
gen.add_title_slide('测试标题', '测试副标题')
gen.add_content_slide('测试内容', ['第一点', '第二点', '第三点'])
gen.save('/tmp/test.pptx')
print('PPT生成成功！')

# 测试模板
templates = PPTTemplate.list_templates()
print(f'可用模板：{len(templates)}')
"
```

---

### 任务2：文档摘要模块

**文件：**
- 创建：`app/document/summarizer.py`
- 创建：`app/services/summary_service.py`
- 修改：`routers/documents.py`

**实现步骤：**

- [ ] **Step 1: 创建摘要生成器**

```python
# app/document/summarizer.py
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

@dataclass
class SummaryResult:
    """摘要结果"""
    original_length: int
    summary_length: int
    compression_ratio: float
    summary_type: str  # "extractive" or "abstractive"
    key_points: List[str]
    full_summary: str

class DocumentSummarizer:
    """文档摘要生成器"""

    def __init__(self):
        self.supported_types = ["pdf", "txt", "md", "docx"]

    async def summarize(
        self,
        text: str,
        method: str = "extractive",
        max_length: int = 200,
        num_sentences: int = 5
    ) -> SummaryResult:
        """生成摘要"""
        if method == "extractive":
            return await self._extractive_summary(text, num_sentences)
        else:
            return await self._abstractive_summary(text, max_length)

    async def _extractive_summary(
        self,
        text: str,
        num_sentences: int = 5
    ) -> SummaryResult:
        """抽取式摘要 - 选取最重要的句子"""
        # 分割句子
        sentences = self._split_sentences(text)

        # 计算句子重要性分数
        scores = self._score_sentences(sentences)

        # 排序并选取前N个
        ranked_indices = sorted(range(len(scores)),
                              key=lambda i: scores[i],
                              reverse=True)[:num_sentences]

        # 保持原始顺序
        ranked_indices.sort()

        # 生成摘要
        summary_sentences = [sentences[i] for i in ranked_indices]
        full_summary = "。".join(summary_sentences)

        return SummaryResult(
            original_length=len(text),
            summary_length=len(full_summary),
            compression_ratio=len(full_summary) / len(text) if len(text) > 0 else 0,
            summary_type="extractive",
            key_points=summary_sentences,
            full_summary=full_summary
        )

    async def _abstractive_summary(
        self,
        text: str,
        max_length: int = 200
    ) -> SummaryResult:
        """生成式摘要 - AI生成新文本"""
        # 简化实现：使用模板 + 关键词提取
        # 实际生产环境应该调用LLM API

        # 提取关键词
        keywords = self._extract_keywords(text, top_n=10)

        # 提取关键句子
        sentences = self._split_sentences(text)
        key_sentences = self._score_sentences(sentences)[:3]

        # 生成摘要
        summary = self._generate_template_summary(text, keywords, key_sentences)

        return SummaryResult(
            original_length=len(text),
            summary_length=len(summary),
            compression_ratio=len(summary) / len(text) if len(text) > 0 else 0,
            summary_type="abstractive",
            key_points=keywords,
            full_summary=summary
        )

    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        # 中文句子分割
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _score_sentences(self, sentences: List[str]) -> List[float]:
        """计算句子重要性分数"""
        scores = []

        for i, sentence in enumerate(sentences):
            score = 0.0

            # 位置分数（开头和结尾的句子通常更重要）
            position = i / max(len(sentences) - 1, 1)
            if position < 0.2 or position > 0.8:
                score += 2.0

            # 长度分数（适中长度的句子更好）
            length = len(sentence)
            if 20 <= length <= 100:
                score += 1.5
            elif length > 200:
                score -= 1.0

            # 关键词分数（包含重要词汇）
            important_words = ['重要', '关键', '主要', '核心', '总结', '结论']
            for word in important_words:
                if word in sentence:
                    score += 1.0

            # 数字分数（通常包含重要数据）
            if re.search(r'\d+', sentence):
                score += 0.5

            scores.append(score)

        return scores

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取关键词"""
        # 简单实现：基于词频
        words = re.findall(r'[\w\u4e00-\u9fff]+', text)

        # 过滤停用词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
                    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去'}

        words = [w for w in words if len(w) >= 2 and w not in stopwords]

        # 统计词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 排序并返回前N个
        sorted_words = sorted(word_freq.items(),
                             key=lambda x: x[1],
                             reverse=True)[:top_n]

        return [word for word, freq in sorted_words]

    def _generate_template_summary(
        self,
        text: str,
        keywords: List[str],
        key_sentences: List[str]
    ) -> str:
        """基于模板生成摘要"""
        # 简化实现
        if key_sentences:
            return " ".join(key_sentences[:3])

        if keywords:
            return f"本文主要讨论了{', '.join(keywords[:5])}等相关内容。"

        return text[:200] + "..."
```

- [ ] **Step 2: 创建结构化摘要生成器**

```python
# app/document/structured_summary.py
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class StructuredSummary:
    """结构化摘要"""
    title: str
    abstract: str
    sections: Dict[str, str]
    key_findings: List[str]
    methodology: str
    conclusions: str
    references: List[str]

class StructuredSummaryGenerator:
    """结构化摘要生成器"""

    def generate(
        self,
        text: str,
        document_type: str = "academic"
    ) -> StructuredSummary:
        """生成结构化摘要"""
        if document_type == "academic":
            return self._academic_summary(text)
        elif document_type == "meeting":
            return self._meeting_summary(text)
        elif document_type == "report":
            return self._report_summary(text)
        else:
            return self._general_summary(text)

    def _academic_summary(self, text: str) -> StructuredSummary:
        """学术论文摘要"""
        return StructuredSummary(
            title=self._extract_title(text),
            abstract=self._generate_abstract(text),
            sections=self._extract_sections(text),
            key_findings=self._extract_findings(text),
            methodology=self._extract_methodology(text),
            conclusions=self._extract_conclusions(text),
            references=self._extract_references(text)
        )

    def _meeting_summary(self, text: str) -> StructuredSummary:
        """会议纪要摘要"""
        return StructuredSummary(
            title="会议纪要",
            abstract=self._summarize_meeting(text),
            sections=self._extract_meeting_sections(text),
            key_findings=self._extract_decisions(text),
            methodology="",
            conclusions=self._extract_action_items(text),
            references=[]
        )

    def _report_summary(self, text: str) -> StructuredSummary:
        """报告摘要"""
        return StructuredSummary(
            title=self._extract_title(text),
            abstract=self._summarize_report(text),
            sections=self._extract_sections(text),
            key_findings=self._extract_metrics(text),
            methodology="",
            conclusions=self._extract_recommendations(text),
            references=[]
        )

    def _general_summary(self, text: str) -> StructuredSummary:
        """通用摘要"""
        return StructuredSummary(
            title="文档摘要",
            abstract=text[:500] if len(text) > 500 else text,
            sections={},
            key_findings=[],
            methodology="",
            conclusions="",
            references=[]
        )

    # 辅助方法...
```

---

### 任务3：会议纪要生成模块

**文件：**
- 创建：`app/document/meeting_minutes.py`
- 创建：`app/services/meeting_service.py`

**实现步骤：**

- [ ] **Step 1: 创建会议纪要生成器**

```python
# app/document/meeting_minutes.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MeetingInfo:
    """会议信息"""
    title: str
    date: str
    time: str
    duration: str
    host: str
    participants: List[str]
    location: str

@dataclass
class DiscussionPoint:
    """讨论要点"""
    topic: str
    speaker: Optional[str]
    content: str
    key_points: List[str]
    timestamp: Optional[str] = None

@dataclass
class ActionItem:
    """待办事项"""
    task: str
    assignee: str
    deadline: str
    priority: str = "medium"
    status: str = "pending"

@dataclass
class MeetingMinutes:
    """会议纪要"""
    meeting_info: MeetingInfo
    agenda: List[str]
    discussion_points: List[DiscussionPoint]
    decisions: List[str]
    action_items: List[ActionItem]
    next_meeting: Optional[Dict]
    generated_at: str

class MeetingMinutesGenerator:
    """会议纪要生成器"""

    def generate_from_text(
        self,
        text: str,
        meeting_date: Optional[str] = None
    ) -> MeetingMinutes:
        """从文本生成会议纪要"""
        # 提取会议信息
        meeting_info = self._extract_meeting_info(text, meeting_date)

        # 提取议程
        agenda = self._extract_agenda(text)

        # 提取讨论要点
        discussion_points = self._extract_discussions(text)

        # 提取决策
        decisions = self._extract_decisions(text)

        # 提取待办事项
        action_items = self._extract_action_items(text)

        return MeetingMinutes(
            meeting_info=meeting_info,
            agenda=agenda,
            discussion_points=discussion_points,
            decisions=decisions,
            action_items=action_items,
            next_meeting=None,
            generated_at=datetime.now().isoformat()
        )

    def _extract_meeting_info(
        self,
        text: str,
        meeting_date: Optional[str]
    ) -> MeetingInfo:
        """提取会议基本信息"""
        # 简化实现：基于规则提取
        # 实际应该用NLP或LLM

        title = "会议纪要"
        date = meeting_date or datetime.now().strftime("%Y-%m-%d")
        time = ""
        duration = ""
        host = ""
        participants = []

        # 提取标题
        lines = text.split('\n')
        for line in lines[:5]:
            if line.strip() and len(line.strip()) < 50:
                title = line.strip()
                break

        return MeetingInfo(
            title=title,
            date=date,
            time=time,
            duration=duration,
            host=host,
            participants=participants,
            location=""
        )

    def _extract_agenda(self, text: str) -> List[str]:
        """提取议程"""
        agenda = []

        # 查找议程关键词
        agenda_keywords = ['议程', 'Agenda', '会议议题']

        lines = text.split('\n')
        in_agenda = False

        for line in lines:
            line = line.strip()

            if any(kw in line for kw in agenda_keywords):
                in_agenda = True
                continue

            if in_agenda:
                if line and not line.startswith('#'):
                    if line.startswith(('1.', '2.', '3.', '•', '-', '·')):
                        agenda.append(line.lstrip('123456789. •-·'))
                    elif len(line) > 10:
                        agenda.append(line)

                if len(agenda) >= 5:
                    break

        return agenda

    def _extract_discussions(self, text: str) -> List[DiscussionPoint]:
        """提取讨论要点"""
        discussions = []

        # 简化实现：基于段落分割
        paragraphs = text.split('\n\n')

        for para in paragraphs:
            if len(para) > 50 and any(kw in para for kw in ['讨论', '认为', '表示', '提出']):
                discussions.append(DiscussionPoint(
                    topic=para[:50] + "...",
                    speaker=None,
                    content=para,
                    key_points=[]
                ))

        return discussions[:10]  # 最多10个讨论点

    def _extract_decisions(self, text: str) -> List[str]:
        """提取决策"""
        decisions = []

        # 查找决策关键词
        decision_keywords = ['决定', '通过', '批准', '同意', '确认', '决策']

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in decision_keywords):
                decisions.append(line)

        return decisions

    def _extract_action_items(self, text: str) -> List[ActionItem]:
        """提取待办事项"""
        action_items = []

        # 查找待办关键词
        todo_keywords = ['待办', 'TODO', '任务', '负责', '完成', '截止']

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in todo_keywords):
                if len(line) > 10:
                    # 简化提取
                    action_items.append(ActionItem(
                        task=line,
                        assignee="",
                        deadline="",
                        priority="medium"
                    ))

        return action_items

    def to_markdown(self, minutes: MeetingMinutes) -> str:
        """转换为Markdown格式"""
        md = f"""# {minutes.meeting_info.title}

## 会议信息
- **日期**: {minutes.meeting_info.date}
- **时间**: {minutes.meeting_info.time}
- **主持人**: {minutes.meeting_info.host}
- **参会人**: {', '.join(minutes.meeting_info.participants)}

## 议程
"""

        for i, item in enumerate(minutes.agenda, 1):
            md += f"{i}. {item}\n"

        md += "\n## 讨论要点\n"
        for point in minutes.discussion_points:
            md += f"### {point.topic}\n{point.content}\n\n"

        md += "\n## 决策\n"
        for decision in minutes.decisions:
            md += f"- {decision}\n"

        md += "\n## 待办事项\n"
        md += "| 任务 | 负责人 | 截止时间 | 优先级 |\n"
        md += "|------|--------|----------|--------|\n"
        for item in minutes.action_items:
            md += f"| {item.task} | {item.assignee} | {item.deadline} | {item.priority} |\n"

        return md

    def to_ppt(self, minutes: MeetingMinutes) -> bytes:
        """转换为PPT"""
        from app.document.ppt_generator import PPTGenerator

        gen = PPTGenerator()
        gen.create_presentation(minutes.meeting_info.title)

        # 标题页
        gen.add_title_slide(
            minutes.meeting_info.title,
            f"{minutes.meeting_info.date} | {minutes.meeting_info.host}"
        )

        # 议程
        gen.add_content_slide("会议议程", minutes.agenda)

        # 讨论要点
        for point in minutes.discussion_points[:5]:
            gen.add_content_slide(point.topic, [point.content])

        # 待办事项
        todo_text = [f"{t.task} - {t.assignee}" for t in minutes.action_items]
        gen.add_content_slide("行动计划", todo_text)

        return gen.get_bytes()
```

---

### 任务4：周报/工作汇报生成模块

**文件：**
- 创建：`app/document/report_generator.py`
- 创建：`app/services/report_service.py`

**实现步骤：**

- [ ] **Step 1: 创建报告生成器**

```python
# app/document/report_generator.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class WorkItem:
    """工作项"""
    title: str
    description: str
    status: str  # completed, in_progress, planned
    category: str  # development, meeting, research, etc.
    hours_spent: Optional[float] = None

@dataclass
class Report:
    """工作报告"""
    title: str
    period: str
    report_type: str  # daily, weekly, monthly
    summary: str
    completed_items: List[WorkItem]
    in_progress_items: List[WorkItem]
    planned_items: List[WorkItem]
    metrics: Dict[str, any]
    challenges: List[str]
    next_plan: List[str]

class ReportGenerator:
    """报告生成器"""

    TEMPLATES = {
        "daily": {
            "name": "日报",
            "sections": ["今日完成", "明日计划", "问题与建议"]
        },
        "weekly": {
            "name": "周报",
            "sections": ["本周完成", "本周进展", "下周计划", "工作指标", "问题与建议"]
        },
        "monthly": {
            "name": "月报",
            "sections": ["本月完成", "本月进展", "下月计划", "KPI完成情况", "问题与建议", "资源需求"]
        }
    }

    def generate(
        self,
        work_items: List[WorkItem],
        report_type: str = "weekly",
        period_start: Optional[str] = None,
        period_end: Optional[str] = None
    ) -> Report:
        """生成工作报告"""
        template = self.TEMPLATES.get(report_type, self.TEMPLATES["weekly"])

        # 分类工作项
        completed = [w for w in work_items if w.status == "completed"]
        in_progress = [w for w in work_items if w.status == "in_progress"]
        planned = [w for w in work_items if w.status == "planned"]

        # 生成摘要
        summary = self._generate_summary(work_items, report_type)

        # 提取指标
        metrics = self._extract_metrics(work_items)

        # 识别挑战
        challenges = self._identify_challenges(work_items)

        # 生成下一步计划
        next_plan = self._generate_next_plan(planned)

        period = self._format_period(period_start, period_end, report_type)

        return Report(
            title=f"{template['name']} - {period}",
            period=period,
            report_type=report_type,
            summary=summary,
            completed_items=completed,
            in_progress_items=in_progress,
            planned_items=planned,
            metrics=metrics,
            challenges=challenges,
            next_plan=next_plan
        )

    def _generate_summary(
        self,
        work_items: List[WorkItem],
        report_type: str
    ) -> str:
        """生成报告摘要"""
        total = len(work_items)
        completed = len([w for w in work_items if w.status == "completed"])

        if report_type == "daily":
            return f"今日完成了{completed}项工作任务。"
        elif report_type == "weekly":
            return f"本周共完成{completed}/{total}项工作任务，整体进度符合预期。"
        else:
            return f"本月共完成{completed}/{total}项工作任务，超额完成月度目标。"

    def _extract_metrics(self, work_items: List[WorkItem]) -> Dict:
        """提取工作指标"""
        total_hours = sum(
            w.hours_spent or 0
            for w in work_items
            if w.hours_spent
        )

        by_category = {}
        for item in work_items:
            cat = item.category
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_items": len(work_items),
            "completed_count": len([w for w in work_items if w.status == "completed"]),
            "total_hours": total_hours,
            "by_category": by_category
        }

    def _identify_challenges(self, work_items: List[WorkItem]) -> List[str]:
        """识别挑战和问题"""
        challenges = []

        # 简化实现：基于关键词
        challenge_keywords = ['困难', '问题', '阻碍', '挑战', '风险']

        for item in work_items:
            if any(kw in item.description for kw in challenge_keywords):
                challenges.append(item.description)

        return challenges[:5]

    def _generate_next_plan(self, planned: List[WorkItem]) -> List[str]:
        """生成下一步计划"""
        return [f"{i+1}. {item.title}" for i, item in enumerate(planned[:5])]

    def _format_period(
        self,
        start: Optional[str],
        end: Optional[str],
        report_type: str
    ) -> str:
        """格式化时间段"""
        if start and end:
            return f"{start} 至 {end}"

        today = datetime.now()

        if report_type == "daily":
            return today.strftime("%Y-%m-%d")
        elif report_type == "weekly":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return f"{week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}"
        else:
            return today.strftime("%Y年%m月")

    def to_markdown(self, report: Report) -> str:
        """转换为Markdown"""
        md = f"""# {report.title}

## 📊 工作概况
{report.summary}

## ✅ 本期完成
"""

        for item in report.completed_items:
            md += f"- **{item.title}**\n  - {item.description}\n"

        if report.in_progress_items:
            md += "\n## 🔄 进行中\n"
            for item in report.in_progress_items:
                md += f"- **{item.title}**\n  - {item.description}\n"

        if report.planned_items:
            md += "\n## 📋 下期计划\n"
            for item in report.planned_items:
                md += f"- **{item.title}**\n  - {item.description}\n"

        if report.metrics:
            md += "\n## 📈 工作指标\n"
            md += f"- 总任务数: {report.metrics.get('total_items', 0)}\n"
            md += f"- 完成数: {report.metrics.get('completed_count', 0)}\n"
            md += f"- 总工时: {report.metrics.get('total_hours', 0)}小时\n"

        if report.challenges:
            md += "\n## ⚠️ 问题与挑战\n"
            for challenge in report.challenges:
                md += f"- {challenge}\n"

        return md

    def to_ppt(self, report: Report) -> bytes:
        """转换为PPT"""
        from app.document.ppt_generator import PPTGenerator

        gen = PPTGenerator()
        gen.create_presentation(report.title)

        # 标题页
        gen.add_title_slide(
            report.title,
            f"类型: {report.report_type}\n周期: {report.period}"
        )

        # 概况
        gen.add_content_slide("工作概况", [report.summary])

        # 完成情况
        completed_text = [item.title for item in report.completed_items]
        gen.add_content_slide("本期完成", completed_text)

        # 下期计划
        if report.planned_items:
            planned_text = [item.title for item in report.planned_items]
            gen.add_content_slide("下期计划", planned_text)

        # 指标
        metrics_text = [
            f"总任务: {report.metrics.get('total_items', 0)}",
            f"已完成: {report.metrics.get('completed_count', 0)}",
            f"总工时: {report.metrics.get('total_hours', 0)}h"
        ]
        gen.add_content_slide("工作指标", metrics_text)

        return gen.get_bytes()
```

---

### 任务5：自动排版模块

**文件：**
- 创建：`app/document/formatter.py`

**实现步骤：**

- [ ] **Step 1: 创建中文排版处理器**

```python
# app/document/formatter.py
import re
from typing import List, Dict

class ChineseTextFormatter:
    """中文文本格式化器 - 基于cjk-text-formatter"""

    def __init__(self):
        self.rules = self._init_rules()

    def _init_rules(self) -> Dict:
        """初始化格式化规则"""
        return {
            "space_rules": {
                "cjk_english": True,      # 中文和英文之间添加空格
                "cjk_number": True,      # 中文和数字之间添加空格
                "english_number": True,  # 英文和数字之间添加空格
            },
            "punctuation_rules": {
                "fix_ellipsis": True,    # 修复省略号
                "fix_quotes": True,      # 修复引号
                "fix_dash": True,        # 修复破折号
            },
            "fullwidth_rules": {
                "letter": True,          # 字母全角转半角
                "number": True,           # 数字全角转半角
            }
        }

    def format(self, text: str, rules: Dict = None) -> str:
        """格式化文本"""
        if rules is None:
            rules = self.rules

        result = text

        # 添加空格
        if rules.get("space_rules", {}).get("cjk_english"):
            result = self._add_cjk_english_space(result)

        if rules.get("space_rules", {}).get("cjk_number"):
            result = self._add_cjk_number_space(result)

        # 修复标点
        if rules.get("punctuation_rules", {}).get("fix_ellipsis"):
            result = self._fix_ellipsis(result)

        if rules.get("punctuation_rules", {}).get("fix_quotes"):
            result = self._fix_quotes(result)

        # 全角转半角
        if rules.get("fullwidth_rules", {}).get("number"):
            result = self._fullwidth_to_halfwidth(result)

        return result

    def _add_cjk_english_space(self, text: str) -> str:
        """在中文和英文之间添加空格"""
        # 中文字符范围: \u4e00-\u9fff
        # 英文字母: a-zA-Z

        pattern = r'([\u4e00-\u9fff])([a-zA-Z])'
        text = re.sub(pattern, r'\1 \2', text)

        pattern = r'([a-zA-Z])([\u4e00-\u9fff])'
        text = re.sub(pattern, r'\1 \2', text)

        return text

    def _add_cjk_number_space(self, text: str) -> str:
        """在中文和数字之间添加空格"""
        # 数字: 0-9

        pattern = r'([\u4e00-\u9fff])([0-9])'
        text = re.sub(pattern, r'\1 \2', text)

        pattern = r'([0-9])([\u4e00-\u9fff])'
        text = re.sub(pattern, r'\1 \2', text)

        return text

    def _fix_ellipsis(self, text: str) -> str:
        """修复省略号"""
        # 替换 ... 或 . . . 为 ……
        text = re.sub(r'\.{3,}', '……', text)
        text = re.sub(r'\.\s\.\s\.', '……', text)

        return text

    def _fix_quotes(self, text: str) -> str:
        """修复引号"""
        # 统一引号格式
        replacements = {
            '"': '"',
            '"': '"',
            ''': ''',
            ''': ''',
            '<': '《',
            '>': '》',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _fullwidth_to_halfwidth(self, text: str) -> str:
        """全角转半角"""
        result = []
        for char in text:
            code = ord(char)
            # 全角数字范围: \uff10-\uff19 (0-9)
            if 0xff10 <= code <= 0xff19:
                result.append(chr(code - 0xfee0))
            else:
                result.append(char)

        return ''.join(result)

    def format_document(
        self,
        text: str,
        formatting_level: str = "standard"
    ) -> str:
        """格式化文档"""
        if formatting_level == "simple":
            return self.format(text, {
                "space_rules": {"cjk_english": True}
            })
        elif formatting_level == "standard":
            return self.format(text)
        else:  # strict
            return self.format(text, {
                "space_rules": {
                    "cjk_english": True,
                    "cjk_number": True,
                    "english_number": True,
                },
                "punctuation_rules": {
                    "fix_ellipsis": True,
                    "fix_quotes": True,
                    "fix_dash": True,
                }
            })
```

---

### 任务6：引用整理模块

**文件：**
- 创建：`app/document/citation_manager.py`

**实现步骤：**

- [ ] **Step 1: 创建引用管理器**

```python
# app/document/citation_manager.py
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Citation:
    """引用文献"""
    citation_id: str
    authors: List[str]
    title: str
    year: str
    source: str  # 期刊、会议、书籍等
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_type: str = "article"  # article, book, conference, website

class CitationManager:
    """引用管理器"""

    def __init__(self):
        self.citations: List[Citation] = []

    def add_citation(self, citation: Citation):
        """添加引用"""
        if not citation.citation_id:
            citation.citation_id = f"ref_{len(self.citations) + 1}"
        self.citations.append(citation)

    def add_from_text(self, text: str):
        """从文本解析添加引用"""
        # 简化实现：基于规则解析
        # 实际应该用NLP

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                citation = self._parse_citation_line(line)
                if citation:
                    self.add_citation(citation)

    def _parse_citation_line(self, line: str) -> Optional[Citation]:
        """解析引用行"""
        # 简化实现：提取年份和标题
        year_match = re.search(r'\((\d{4})\)|\b(19|20)\d{2}\b', line)

        if year_match:
            year = year_match.group(1) or year_match.group(2)
        else:
            year = ""

        # 提取标题（假设在引号或书名号中）
        title_match = re.search(r'《(.+?)》|"(.+?)"|"(.+?)"', line)
        title = title_match.group(1) or title_match.group(2) or title_match.group(3) or line[:50]

        return Citation(
            citation_id="",
            authors=[],
            title=title,
            year=year,
            source=""
        )

    def format_bibliography(
        self,
        style: str = "apa"
    ) -> str:
        """格式化参考文献"""
        if style == "apa":
            return self._format_apa()
        elif style == "gbt":
            return self._format_gbt7714()  # 中国国家标准
        else:
            return self._format_simple()

    def _format_apa(self) -> str:
        """APA格式"""
        references = []

        for i, cite in enumerate(self.citations, 1):
            authors = ", ".join(cite.authors) if cite.authors else "Anonymous"

            ref = f"{authors} ({cite.year}). {cite.title}."

            if cite.source:
                ref += f" *{cite.source}*"
                if cite.volume:
                    ref += f", {cite.volume}"
                if cite.issue:
                    ref += f"({cite.issue})"
                if cite.pages:
                    ref += f", {cite.pages}"

            if cite.doi:
                ref += f" https://doi.org/{cite.doi}"

            references.append(ref)

        return "\n\n".join(references)

    def _format_gbt7714(self) -> str:
        """GB/T 7714格式（中国国家标准）"""
        references = []

        for cite in self.citations:
            authors = " ".join(cite.authors) if cite.authors else ""

            ref = f"{authors}. {cite.title}."

            if cite.source:
                ref += f" {cite.source}"
                if cite.volume:
                    ref += f", {cite.volume}"
                if cite.issue:
                    ref += f"({cite.issue})"
                if cite.pages:
                    ref += f": {cite.pages}"

            ref += f". {cite.year}."

            if cite.doi:
                ref += f" DOI:{cite.doi}"

            references.append(ref)

        return "\n\n".join(references)

    def _format_simple(self) -> str:
        """简化格式"""
        references = []

        for i, cite in enumerate(self.citations, 1):
            ref = f"[{i}] {cite.title} - {cite.authors}, {cite.year}"
            references.append(ref)

        return "\n".join(references)

    def get_citation_count(self) -> int:
        """获取引用数量"""
        return len(self.citations)

    def export_json(self) -> str:
        """导出为JSON"""
        import json

        data = [
            {
                "citation_id": c.citation_id,
                "authors": c.authors,
                "title": c.title,
                "year": c.year,
                "source": c.source,
                "citation_type": c.citation_type
            }
            for c in self.citations
        ]

        return json.dumps(data, ensure_ascii=False, indent=2)
```

---

## 📦 依赖项

需要添加到 `requirements.txt` 的包：

```txt
# 文档处理
python-pptx>=0.6.21
pdfplumber>=0.10.0
python-docx>=0.8.11

# 文本处理
jieba>=0.42.1  # 中文分词
textract>=1.6.5  # 文档文本提取
```

---

## ✅ 验证清单

完成实现后，需要验证：

- [ ] PPT生成功能正常
- [ ] 文档摘要生成正常
- [ ] 会议纪要生成正常
- [ ] 周报生成正常
- [ ] 自动排版功能正常
- [ ] 引用整理功能正常
- [ ] API接口可访问
- [ ] 错误处理完善
- [ ] 文档齐全

---

## 🚀 后续扩展建议

1. **集成LLM**：添加GPT/Claude API调用实现更智能的内容生成
2. **模板市场**：创建在线模板市场
3. **批量处理**：支持批量文档处理
4. **格式转换**：支持更多格式（HTML, Markdown, LaTeX）
5. **团队协作**：添加批注、评论功能
