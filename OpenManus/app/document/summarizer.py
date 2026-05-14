"""
文档摘要模块
提供抽取式和生成式文档摘要功能
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from collections import Counter


@dataclass
class SummaryResult:
    """摘要结果"""
    original_length: int
    summary_length: int
    compression_ratio: float
    summary_type: str
    key_points: List[str]
    full_summary: str
    keywords: List[str]


class DocumentSummarizer:
    """文档摘要生成器"""

    def __init__(self):
        self.supported_types = ["pdf", "txt", "md", "docx"]
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他',
            '她', '它', '们', '这个', '那个', '什么', '怎么', '为什么'
        }

    async def summarize(
        self,
        text: str,
        method: str = "extractive",
        max_length: int = 200,
        num_sentences: int = 5
    ) -> SummaryResult:
        """生成摘要"""
        if not text or not text.strip():
            return SummaryResult(
                original_length=0,
                summary_length=0,
                compression_ratio=0,
                summary_type=method,
                key_points=[],
                full_summary="",
                keywords=[]
            )

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
        sentences = self._split_sentences(text)

        if not sentences:
            sentences = [text]

        scores = self._score_sentences(sentences, text)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:min(num_sentences, len(sentences))]

        ranked_indices.sort()

        summary_sentences = [sentences[i] for i in ranked_indices]
        full_summary = "。".join(summary_sentences)

        if not full_summary.endswith('。') and summary_sentences:
            full_summary += "。"

        keywords = self._extract_keywords(text, top_n=10)

        return SummaryResult(
            original_length=len(text),
            summary_length=len(full_summary),
            compression_ratio=len(full_summary) / len(text) if len(text) > 0 else 0,
            summary_type="extractive",
            key_points=summary_sentences,
            full_summary=full_summary,
            keywords=keywords
        )

    async def _abstractive_summary(
        self,
        text: str,
        max_length: int = 200
    ) -> SummaryResult:
        """生成式摘要 - AI生成新文本（简化实现）"""
        sentences = self._split_sentences(text)

        keywords = self._extract_keywords(text, top_n=10)

        top_sentences = sentences[:3] if len(sentences) > 3 else sentences

        summary = self._generate_summary_from_keywords(text, keywords, top_sentences)

        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return SummaryResult(
            original_length=len(text),
            summary_length=len(summary),
            compression_ratio=len(summary) / len(text) if len(text) > 0 else 0,
            summary_type="abstractive",
            key_points=keywords[:5],
            full_summary=summary,
            keywords=keywords
        )

    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        text = text.replace('\n', '。')
        sentences = re.split(r'[。！？；\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences

    def _score_sentences(self, sentences: List[str], full_text: str) -> List[float]:
        """计算句子重要性分数"""
        scores = []

        keywords = set(self._extract_keywords(full_text, top_n=20))

        for i, sentence in enumerate(sentences):
            score = 0.0

            position = i / max(len(sentences) - 1, 1)
            if position < 0.15:
                score += 3.0
            elif position > 0.85:
                score += 2.0

            length = len(sentence)
            if 20 <= length <= 100:
                score += 2.0
            elif 100 < length <= 200:
                score += 1.5
            elif length > 300:
                score -= 1.0

            sentence_lower = sentence.lower()
            important_words = ['重要', '关键', '主要', '核心', '总结', '结论',
                             '因此', '所以', '研究发现', '数据表明', '结果显示']
            for word in important_words:
                if word in sentence:
                    score += 1.5

            for keyword in keywords:
                if keyword in sentence:
                    score += 0.5

            if re.search(r'\d+', sentence):
                score += 0.8

            if '。' in sentence and len(sentence) > 50:
                score += 1.0

            scores.append(score)

        return scores

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取关键词"""
        words = re.findall(r'[\w\u4e00-\u9fff]+', text)
        words = [w for w in words if len(w) >= 2 and w not in self.stopwords]

        word_freq = Counter(words)
        sorted_words = word_freq.most_common(top_n * 2)

        keywords = []
        seen = set()
        for word, freq in sorted_words:
            if freq >= 2 and word not in seen:
                keywords.append(word)
                seen.add(word)
                if len(keywords) >= top_n:
                    break

        return keywords

    def _generate_summary_from_keywords(
        self,
        text: str,
        keywords: List[str],
        top_sentences: List[str]
    ) -> str:
        """基于关键词和关键句生成摘要"""
        summary_parts = []

        if keywords:
            keyword_str = "、".join(keywords[:5])
            summary_parts.append(f"本文主要围绕{keyword_str}等核心内容展开论述。")

        if top_sentences:
            summary_parts.append(top_sentences[0])

        summary_parts.append("综上所述，相关领域取得了重要进展。")

        return "".join(summary_parts)


class StructuredSummaryGenerator:
    """结构化摘要生成器"""

    def generate(
        self,
        text: str,
        document_type: str = "general"
    ) -> Dict:
        """生成结构化摘要"""
        if document_type == "academic":
            return self._academic_summary(text)
        elif document_type == "meeting":
            return self._meeting_summary(text)
        elif document_type == "report":
            return self._report_summary(text)
        else:
            return self._general_summary(text)

    def _academic_summary(self, text: str) -> Dict:
        """学术论文摘要"""
        summarizer = DocumentSummarizer()

        return {
            "type": "academic",
            "title": self._extract_title(text),
            "abstract": self._generate_abstract(text),
            "background": self._extract_section(text, ['背景', '引言', '研究背景']),
            "methodology": self._extract_section(text, ['方法', ' Methodology']),
            "results": self._extract_section(text, ['结果', '实验', ' Findings']),
            "conclusion": self._extract_section(text, ['结论', '总结', 'Conclusion']),
            "keywords": summarizer._extract_keywords(text, 10)
        }

    def _meeting_summary(self, text: str) -> Dict:
        """会议纪要摘要"""
        return {
            "type": "meeting",
            "meeting_title": self._extract_meeting_title(text),
            "date": self._extract_date(text),
            "participants": self._extract_participants(text),
            "agenda": self._extract_agenda(text),
            "decisions": self._extract_decisions(text),
            "action_items": self._extract_action_items(text)
        }

    def _report_summary(self, text: str) -> Dict:
        """报告摘要"""
        summarizer = DocumentSummarizer()

        return {
            "type": "report",
            "title": self._extract_title(text),
            "summary": self._generate_summary(text),
            "key_metrics": self._extract_metrics(text),
            "main_points": self._extract_main_points(text),
            "recommendations": self._extract_recommendations(text)
        }

    def _general_summary(self, text: str) -> Dict:
        """通用摘要"""
        summarizer = DocumentSummarizer()

        return {
            "type": "general",
            "title": self._extract_title(text),
            "summary": self._generate_summary(text),
            "keywords": summarizer._extract_keywords(text, 10),
            "key_points": self._extract_key_points(text)
        }

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and 5 < len(line) < 100:
                line = re.sub(r'^[#一二三四五六]+\.?\s*', '', line)
                return line
        return "文档标题"

    def _extract_date(self, text: str) -> str:
        """提取日期"""
        date_pattern = r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)'
        match = re.search(date_pattern, text)
        return match.group(1) if match else ""

    def _extract_participants(self, text: str) -> List[str]:
        """提取参会人"""
        participants = []
        patterns = ['参会人员[：:](.+?)(?:\n|$)', '参会者[：:](.+?)(?:\n|$)',
                    '参与人[：:](.+?)(?:\n|$)']

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                participants = [p.strip() for p in match.group(1).split(',')]
                break

        return participants

    def _extract_agenda(self, text: str) -> List[str]:
        """提取议程"""
        agenda = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if any(kw in line for kw in ['议程', 'Agenda', '会议议题']):
                continue
            if line.startswith(('1.', '2.', '3.', '•', '-', '·', '▸')):
                agenda.append(line.lstrip('123456789. •-·▸').strip())

            if len(agenda) >= 5:
                break

        return agenda

    def _extract_decisions(self, text: str) -> List[str]:
        """提取决策"""
        decisions = []
        decision_keywords = ['决定', '通过', '批准', '同意', '确认', '决策', '共识']

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in decision_keywords) and len(line) > 10:
                decisions.append(line)

        return decisions[:10]

    def _extract_action_items(self, text: str) -> List[Dict]:
        """提取待办事项"""
        action_items = []
        patterns = [
            r'待办[：:]?\s*(.+?)(?:\n|$)',
            r'TODO[：:]?\s*(.+?)(?:\n|$)',
            r'任务[：:]?\s*(.+?)(?:\n|$)',
            r'负责[：:]?\s*(.+?)[，,]\s*(.+?)(?:\n|$)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    action_items.append({
                        'task': match[0].strip(),
                        'assignee': match[1].strip() if len(match) > 1 else '',
                        'deadline': ''
                    })
                else:
                    action_items.append({
                        'task': match.strip(),
                        'assignee': '',
                        'deadline': ''
                    })

        return action_items[:10]

    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """提取指定章节"""
        for keyword in keywords:
            pattern = f'{keyword}[：:]?\\s*([^#\\n]+?)(?=\\n\\s*[#一二三四]|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:500]

        return ""

    def _extract_metrics(self, text: str) -> Dict:
        """提取关键指标"""
        metrics = {}

        number_pattern = r'([\u4e00-\u9fff\d]+)[：:]\s*(\d+(?:\.\d+)?%?)'
        matches = re.findall(number_pattern, text)

        for label, value in matches[:10]:
            metrics[label] = value

        return metrics

    def _extract_recommendations(self, text: str) -> List[str]:
        """提取建议"""
        recommendations = []
        rec_keywords = ['建议', '推荐', '提出', '认为应该', '应当', '可以考虑']

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in rec_keywords) and len(line) > 10:
                recommendations.append(line)

        return recommendations[:5]

    def _extract_key_points(self, text: str) -> List[str]:
        """提取关键点"""
        summarizer = DocumentSummarizer()

        sentences = summarizer._split_sentences(text)
        if sentences:
            sentences = [s for s in sentences if len(s) > 20]

        return sentences[:7] if len(sentences) > 7 else sentences

    def _generate_abstract(self, text: str) -> str:
        """生成摘要"""
        summarizer = DocumentSummarizer()
        result = summarizer._extractive_summary(text, num_sentences=3)
        return result.full_summary

    def _generate_summary(self, text: str) -> str:
        """生成总结"""
        summarizer = DocumentSummarizer()
        result = summarizer._extractive_summary(text, num_sentences=5)
        return result.full_summary

    def _extract_main_points(self, text: str) -> List[str]:
        """提取主要观点"""
        summarizer = DocumentSummarizer()

        sentences = summarizer._split_sentences(text)
        scores = summarizer._score_sentences(sentences, text)

        ranked_indices = sorted(range(len(scores)),
                              key=lambda i: scores[i],
                              reverse=True)[:5]
        ranked_indices.sort()

        return [sentences[i] for i in ranked_indices if i < len(sentences)]

    def _extract_meeting_title(self, text: str) -> str:
        """提取会议标题"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 100:
                line = re.sub(r'^[#会议纪要]+', '', line)
                return line
        return "会议纪要"
