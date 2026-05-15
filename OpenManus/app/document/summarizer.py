"""
文档摘要模块
提供抽取式和生成式文档摘要功能
支持学术论文专用提取、引用格式支持、中英文混合处理
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import re
from collections import Counter
from enum import Enum


class DocumentType(str, Enum):
    """文档类型枚举"""
    GENERAL = "general"
    ACADEMIC = "academic"
    MEETING = "meeting"
    REPORT = "report"
    NEWS = "news"
    TECHNICAL = "technical"


class CitationStyle(str, Enum):
    """引用格式枚举"""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    GB7714 = "gb7714"


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
    document_type: str = DocumentType.GENERAL
    confidence: float = 0.0


@dataclass
class AcademicCitation:
    """学术引用"""
    authors: List[str]
    year: str
    title: str
    journal: str
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None

    def format(self, style: CitationStyle = CitationStyle.APA) -> str:
        """格式化引用"""
        if style == CitationStyle.APA:
            return self._format_apa()
        elif style == CitationStyle.MLA:
            return self._format_mla()
        elif style == CitationStyle.GB7714:
            return self._format_gb7714()
        else:
            return self._format_apa()

    def _format_apa(self) -> str:
        """APA格式"""
        authors = self._format_authors_apa()
        parts = [f"{authors} ({self.year})"]
        if self.title:
            parts.append(f"{self.title}.")
        if self.journal:
            journal_part = self.journal
            if self.volume:
                journal_part += f", {self.volume}"
                if self.issue:
                    journal_part += f"({self.issue})"
            parts.append(journal_part)
        if self.pages:
            parts.append(f"pp. {self.pages}")
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")
        return " ".join(parts)

    def _format_mla(self) -> str:
        """MLA格式"""
        authors = self._format_authors_mla()
        parts = [f"{authors}. {self.title}."]
        if self.journal:
            journal_part = f"{self.journal}"
            if self.volume:
                journal_part += f", vol. {self.volume}"
            if self.year:
                journal_part += f", {self.year}"
            if self.pages:
                journal_part += f", pp. {self.pages}"
            parts.append(journal_part)
        return " ".join(parts)

    def _format_gb7714(self) -> str:
        """GB/T 7714格式"""
        authors = "; ".join(self.authors) if len(self.authors) > 1 else self.authors[0] if self.authors else ""
        parts = [f"{authors}.{self.title}[J]."]
        if self.journal:
            parts.append(self.journal)
        if self.year:
            parts.append(f"{self.year},")
        if self.volume:
            parts.append(f"{self.volume}")
            if self.issue:
                parts.append(f"({self.issue})")
        if self.pages:
            parts.append(f":{self.pages}.")
        return "".join(parts)

    def _format_authors_apa(self) -> str:
        """APA格式作者列表"""
        if not self.authors:
            return "Anonymous"
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) == 2:
            return " & ".join(self.authors)
        if len(self.authors) <= 5:
            return ", ".join(self.authors[:-1]) + ", & " + self.authors[-1]
        return self.authors[0] + " et al."

    def _format_authors_mla(self) -> str:
        """MLA格式作者列表"""
        if not self.authors:
            return "Anonymous"
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return self.authors[0] + " et al."


@dataclass
class AcademicMetadata:
    """学术论文元数据"""
    title: str = ""
    authors: List[str] = None
    affiliations: List[str] = None
    abstract: str = ""
    keywords: List[str] = None
    citations: List[AcademicCitation] = None
    references_count: int = 0
    publication_date: str = ""
    journal_name: str = ""
    doi: str = ""
    fund_project: str = ""
    first_author: str = ""
    corresponding_author: str = ""

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.affiliations is None:
            self.affiliations = []
        if self.keywords is None:
            self.keywords = []
        if self.citations is None:
            self.citations = []


class DocumentSummarizer:
    """文档摘要生成器"""

    def __init__(self):
        self.supported_types = ["pdf", "txt", "md", "docx"]
        self.stopwords = {
            'zh': {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
                   '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                   '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他',
                   '她', '它', '们', '这个', '那个', '什么', '怎么', '为什么'},
            'en': {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                   'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                   'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                   'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                   'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
                   'below', 'between', 'under', 'again', 'further', 'then', 'once',
                   'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
                   'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                   'own', 'same', 'so', 'than', 'too', 'very', 'just', 'or', 'and', 'but',
                   'if', 'because', 'while', 'although', 'though', 'that', 'which', 'who'}
        }
        self.academic_section_keywords = {
            'zh': {'摘要': ['摘要', 'Abstract'],
                   '引言': ['引言', '引言部分', 'Introduction', '背景'],
                   '方法': ['方法', '实验方法', '研究方法', 'Materials and Methods', 'Methodology'],
                   '结果': ['结果', '实验结果', 'Results', '研究结果'],
                   '讨论': ['讨论', '讨论部分', 'Discussion'],
                   '结论': ['结论', '总结', 'Conclusion', '结语'],
                   '参考文献': ['参考文献', 'References', '引用', '参考资料']},
            'en': {'Abstract': ['Abstract', 'Summary'],
                   'Introduction': ['Introduction', 'Background', 'Introduction section'],
                   'Methods': ['Methods', 'Experimental methods', 'Methodology', 'Materials and Methods'],
                   'Results': ['Results', 'Experimental results', 'Findings'],
                   'Discussion': ['Discussion', 'Discussion section'],
                   'Conclusion': ['Conclusion', 'Summary', 'Conclusions'],
                   'References': ['References', 'Bibliography', 'Citations']}
        }

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        zh_chars = re.findall(r'[\u4e00-\u9fff]', text)
        en_words = re.findall(r'[a-zA-Z]+', text)
        
        if len(zh_chars) > len(en_words) * 2:
            return 'zh'
        elif len(en_words) > len(zh_chars) * 2:
            return 'en'
        else:
            return 'mixed'

    async def summarize(
        self,
        text: str,
        method: str = "extractive",
        max_length: int = 200,
        num_sentences: int = 5,
        document_type: str = "general"
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
                keywords=[],
                document_type=document_type,
                confidence=0.0
            )

        if document_type == "academic":
            return await self._academic_summarize(text, method, max_length, num_sentences)

        if method == "extractive":
            return await self._extractive_summary(text, num_sentences)
        else:
            return await self._abstractive_summary(text, max_length)

    async def _academic_summarize(
        self,
        text: str,
        method: str,
        max_length: int,
        num_sentences: int
    ) -> SummaryResult:
        """学术论文专用摘要"""
        lang = self._detect_language(text)
        metadata = self._extract_academic_metadata(text, lang)
        
        keywords = self._extract_keywords(text, top_n=15, lang=lang)
        
        if metadata.abstract:
            full_summary = metadata.abstract[:max_length]
            if len(metadata.abstract) > max_length:
                full_summary += "..."
        elif method == "extractive":
            result = await self._extractive_summary(text, num_sentences)
            full_summary = result.full_summary
        else:
            result = await self._abstractive_summary(text, max_length)
            full_summary = result.full_summary

        key_points = self._extract_academic_key_points(text, lang)
        
        confidence = self._calculate_confidence(text, metadata, keywords)

        return SummaryResult(
            original_length=len(text),
            summary_length=len(full_summary),
            compression_ratio=len(full_summary) / len(text) if len(text) > 0 else 0,
            summary_type="academic_" + method,
            key_points=key_points,
            full_summary=full_summary,
            keywords=keywords,
            document_type=DocumentType.ACADEMIC,
            confidence=confidence
        )

    def _extract_academic_metadata(self, text: str, lang: str) -> AcademicMetadata:
        """提取学术论文元数据"""
        metadata = AcademicMetadata()
        
        metadata.title = self._extract_title(text)
        metadata.authors = self._extract_authors(text, lang)
        metadata.abstract = self._extract_section_content(text, '摘要' if lang == 'zh' else 'Abstract', lang)
        metadata.keywords = self._extract_keywords(text, top_n=8, lang=lang)
        metadata.citations = self._extract_citations(text)
        metadata.references_count = len(metadata.citations)
        metadata.publication_date = self._extract_publication_date(text)
        metadata.journal_name = self._extract_journal_name(text)
        metadata.doi = self._extract_doi(text)
        metadata.fund_project = self._extract_fund_project(text, lang)
        
        if metadata.authors:
            metadata.first_author = metadata.authors[0]

        return metadata

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        lines = text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if line and 5 < len(line) < 200:
                line = re.sub(r'^[#一二三四五六]+\.?\s*', '', line)
                return line.strip()
        return "文档标题"

    def _extract_authors(self, text: str, lang: str) -> List[str]:
        """提取作者"""
        authors = []
        
        patterns = [
            r'[作者Author][：:]\s*(.+?)(?:\n|$)',
            r'([\u4e00-\u9fff]{2,4}(?:[\s,，、][\u4e00-\u9fff]{2,4})+)',
            r'([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+(?:,\s*[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:2000])
            if match:
                author_text = match.group(1)
                separators = r'[,，、;；\s]+'
                potential_authors = [a.strip() for a in re.split(separators, author_text) if a.strip()]
                
                valid_authors = []
                for author in potential_authors[:10]:
                    if re.match(r'^[\u4e00-\u9fff]{2,4}$', author) or re.match(r'^[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+$', author):
                        valid_authors.append(author)
                if valid_authors:
                    authors = valid_authors
                    break
        
        return authors

    def _extract_section_content(self, text: str, section_name: str, lang: str) -> str:
        """提取指定章节内容"""
        keywords = self.academic_section_keywords.get(lang, self.academic_section_keywords['zh']).get(section_name, [section_name])
        
        for keyword in keywords:
            pattern = rf'{keyword}[：:]?\s*([^#\n]+?)(?=\n\s*[#一二三四五]|References|参考文献|\n\n\n|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                return re.sub(r'\s+', ' ', content)[:2000]
        
        return ""

    def _extract_citations(self, text: str) -> List[AcademicCitation]:
        """提取引用"""
        citations = []
        
        apa_pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*\((\d{4})\)\s*([^.,]+?)\.?\s*(?:([A-Z][a-zA-Z]+(?:\s+[A-Za-z]+)*))?'
        gb_pattern = r'([\u4e00-\u9fff]{2,4}(?:[\s,，][\u4e00-\u9fff]{2,4})+)\s*\.?\s*([^\n]+?)\[([A-Za-z]+)\]'
        
        matches = re.findall(apa_pattern, text)
        for match in matches:
            if len(match) >= 3:
                citations.append(AcademicCitation(
                    authors=[match[0].strip()],
                    year=match[1],
                    title=match[2].strip(),
                    journal=match[3].strip() if len(match) > 3 else ""
                ))
        
        matches = re.findall(gb_pattern, text)
        for match in matches:
            authors = [a.strip() for a in re.split(r'[,，、]', match[0]) if a.strip()]
            citations.append(AcademicCitation(
                authors=authors[:5],
                year="",
                title=match[1].strip(),
                journal=""
            ))
        
        return citations[:20]

    def _extract_publication_date(self, text: str) -> str:
        """提取发表日期"""
        patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{4}-\d{2}-\d{2})',
            r'Published:\s*(\d{4}-\d{2}-\d{2})',
            r'出版时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""

    def _extract_journal_name(self, text: str) -> str:
        """提取期刊名称"""
        patterns = [
            r'期刊[：:]\s*(.+?)(?:\n|$)',
            r'Journal[：:]\s*(.+?)(?:\n|$)',
            r'发表于[：:]\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""

    def _extract_doi(self, text: str) -> str:
        """提取DOI"""
        pattern = r'DOI\s*[：:]\s*(\d+\.\d+/[\w.-]+)'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return ""

    def _extract_fund_project(self, text: str, lang: str) -> str:
        """提取基金项目"""
        patterns = [
            r'基金项目[：:]\s*(.+?)(?:\n|$)',
            r'Funding[：:]\s*(.+?)(?:\n|$)',
            r'资助项目[：:]\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""

    def _extract_academic_key_points(self, text: str, lang: str) -> List[str]:
        """提取学术关键点"""
        points = []
        
        if lang == 'zh' or lang == 'mixed':
            sections = ['摘要', '引言', '方法', '结果', '讨论', '结论']
        else:
            sections = ['Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion']
        
        for section in sections:
            content = self._extract_section_content(text, section, lang)
            if content:
                sentences = self._split_sentences(content)
                if sentences:
                    points.append(f"{section}: {sentences[0][:50]}...")
        
        return points

    def _calculate_confidence(self, text: str, metadata: AcademicMetadata, keywords: List[str]) -> float:
        """计算摘要置信度"""
        score = 0.5
        
        if metadata.abstract:
            score += 0.2
        
        if metadata.authors:
            score += 0.1
        
        if metadata.doi:
            score += 0.1
        
        if len(keywords) >= 5:
            score += 0.1
        
        return min(score, 1.0)

    async def _extractive_summary(
        self,
        text: str,
        num_sentences: int = 5
    ) -> SummaryResult:
        """抽取式摘要 - 选取最重要的句子"""
        lang = self._detect_language(text)
        sentences = self._split_sentences(text, lang)

        if not sentences:
            sentences = [text]

        scores = self._score_sentences(sentences, text, lang)

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

        keywords = self._extract_keywords(text, top_n=10, lang=lang)

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
        """生成式摘要"""
        lang = self._detect_language(text)
        sentences = self._split_sentences(text, lang)

        keywords = self._extract_keywords(text, top_n=10, lang=lang)

        top_sentences = sentences[:3] if len(sentences) > 3 else sentences

        summary = self._generate_summary_from_keywords(text, keywords, top_sentences, lang)

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

    def _split_sentences(self, text: str, lang: str = 'zh') -> List[str]:
        """分割句子"""
        text = text.replace('\n', '。')
        
        if lang == 'zh' or lang == 'mixed':
            sentences = re.split(r'[。！？；\n]+', text)
        else:
            sentences = re.split(r'[.!?;\n]+', text)
        
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences

    def _score_sentences(self, sentences: List[str], full_text: str, lang: str) -> List[float]:
        """计算句子重要性分数"""
        scores = []
        stopwords = self.stopwords.get(lang, self.stopwords['zh'])
        keywords = set(self._extract_keywords(full_text, top_n=20, lang=lang))

        for i, sentence in enumerate(sentences):
            score = 0.0

            position = i / max(len(sentences) - 1, 1)
            if position < 0.15:
                score += 3.0
            elif position > 0.85:
                score += 2.0

            length = len(sentence)
            if 20 <= length <= 150:
                score += 2.0
            elif 150 < length <= 300:
                score += 1.5
            elif length > 500:
                score -= 1.0

            important_words = {
                'zh': ['重要', '关键', '主要', '核心', '总结', '结论', '因此', '所以', '研究发现', '数据表明', '结果显示', '提出', '表明', '指出'],
                'en': ['important', 'key', 'main', 'core', 'summary', 'conclusion', 'therefore', 'thus', 'research shows', 'data indicates', 'results show', 'suggests', 'indicates'],
                'mixed': ['重要', '关键', '核心', 'important', 'key', 'main', 'conclusion', '结论', '研究', 'research', '结果', 'results']
            }
            
            for word in important_words.get(lang, important_words['zh']):
                if word in sentence.lower():
                    score += 1.5

            sentence_lower = sentence.lower()
            for keyword in keywords:
                if keyword.lower() in sentence_lower:
                    score += 0.5

            if re.search(r'\d+', sentence):
                score += 0.8

            if sentence.count('。') >= 2 and len(sentence) > 50:
                score += 1.0

            scores.append(score)

        return scores

    def _extract_keywords(self, text: str, top_n: int = 10, lang: str = 'zh') -> List[str]:
        """提取关键词"""
        stopwords = self.stopwords.get(lang, self.stopwords['zh'])
        
        if lang == 'zh' or lang == 'mixed':
            words = re.findall(r'[\w\u4e00-\u9fff]+', text)
        else:
            words = re.findall(r'[a-zA-Z]+', text)
        
        words = [w for w in words if len(w) >= 2 and w.lower() not in stopwords]

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
        top_sentences: List[str],
        lang: str
    ) -> str:
        """基于关键词和关键句生成摘要"""
        summary_parts = []

        if keywords:
            if lang == 'zh' or lang == 'mixed':
                keyword_str = "、".join(keywords[:5])
                summary_parts.append(f"本文主要围绕{keyword_str}等核心内容展开论述。")
            else:
                keyword_str = ", ".join(keywords[:5])
                summary_parts.append(f"This article focuses on {keyword_str} and other core topics.")

        if top_sentences:
            summary_parts.append(top_sentences[0][:100])

        if lang == 'zh' or lang == 'mixed':
            summary_parts.append("综上所述，相关领域取得了重要进展。")
        else:
            summary_parts.append("In summary, significant progress has been made in this field.")

        return "".join(summary_parts)


class StructuredSummaryGenerator:
    """结构化摘要生成器"""

    def generate(
        self,
        text: str,
        document_type: str = "general",
        citation_style: str = "apa"
    ) -> Dict:
        """生成结构化摘要"""
        if document_type == "academic":
            return self._academic_summary(text, citation_style)
        elif document_type == "meeting":
            return self._meeting_summary(text)
        elif document_type == "report":
            return self._report_summary(text)
        elif document_type == "news":
            return self._news_summary(text)
        else:
            return self._general_summary(text)

    def _academic_summary(self, text: str, citation_style: str) -> Dict:
        """学术论文摘要"""
        summarizer = DocumentSummarizer()
        lang = summarizer._detect_language(text)
        
        metadata = summarizer._extract_academic_metadata(text, lang)
        
        citations_formatted = []
        for citation in metadata.citations[:5]:
            style = CitationStyle(citation_style)
            citations_formatted.append(citation.format(style))

        return {
            "type": "academic",
            "title": metadata.title,
            "authors": metadata.authors,
            "first_author": metadata.first_author,
            "corresponding_author": metadata.corresponding_author,
            "affiliations": metadata.affiliations,
            "abstract": metadata.abstract[:1000],
            "keywords": metadata.keywords,
            "journal": metadata.journal_name,
            "publication_date": metadata.publication_date,
            "doi": metadata.doi,
            "fund_project": metadata.fund_project,
            "references_count": metadata.references_count,
            "sample_citations": citations_formatted,
            "background": summarizer._extract_section_content(text, '引言', lang),
            "methodology": summarizer._extract_section_content(text, '方法', lang),
            "results": summarizer._extract_section_content(text, '结果', lang),
            "conclusion": summarizer._extract_section_content(text, '结论', lang),
            "detected_language": lang
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
            "recommendations": self._extract_recommendations(text),
            "keywords": summarizer._extract_keywords(text, 10)
        }

    def _news_summary(self, text: str) -> Dict:
        """新闻摘要"""
        summarizer = DocumentSummarizer()
        lang = summarizer._detect_language(text)
        
        return {
            "type": "news",
            "title": self._extract_title(text),
            "summary": self._generate_summary(text),
            "keywords": summarizer._extract_keywords(text, 8),
            "date": self._extract_date(text),
            "source": self._extract_source(text),
            "detected_language": lang
        }

    def _general_summary(self, text: str) -> Dict:
        """通用摘要"""
        summarizer = DocumentSummarizer()
        lang = summarizer._detect_language(text)

        return {
            "type": "general",
            "title": self._extract_title(text),
            "summary": self._generate_summary(text),
            "keywords": summarizer._extract_keywords(text, 10),
            "key_points": self._extract_key_points(text),
            "detected_language": lang
        }

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and 5 < len(line) < 150:
                line = re.sub(r'^[#一二三四五六]+\.?\s*', '', line)
                return line
        return "文档标题"

    def _extract_date(self, text: str) -> str:
        """提取日期"""
        date_pattern = r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)'
        match = re.search(date_pattern, text)
        return match.group(1) if match else ""

    def _extract_source(self, text: str) -> str:
        """提取来源"""
        patterns = [
            r'来源[：:]\s*(.+?)(?:\n|$)',
            r'Source[：:]\s*(.+?)(?:\n|$)',
            r'来源网站[：:]\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""

    def _extract_participants(self, text: str) -> List[str]:
        """提取参会人"""
        participants = []
        patterns = ['参会人员[：:](.+?)(?:\n|$)', '参会者[：:](.+?)(?:\n|$)',
                    '参与人[：:](.+?)(?:\n|$)', 'Participants[：:](.+?)(?:\n|$)']

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

            if len(agenda) >= 8:
                break

        return agenda

    def _extract_decisions(self, text: str) -> List[str]:
        """提取决策"""
        decisions = []
        decision_keywords = ['决定', '通过', '批准', '同意', '确认', '决策', '共识', 'decide', 'approve', 'agree']

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
                return match.group(1).strip()[:800]

        return ""

    def _extract_metrics(self, text: str) -> Dict:
        """提取关键指标"""
        metrics = {}

        number_pattern = r'([\u4e00-\u9fff\d]+)[：:]\s*(\d+(?:\.\d+)?%?)'
        matches = re.findall(number_pattern, text)

        for label, value in matches[:15]:
            metrics[label] = value

        return metrics

    def _extract_recommendations(self, text: str) -> List[str]:
        """提取建议"""
        recommendations = []
        rec_keywords = ['建议', '推荐', '提出', '认为应该', '应当', '可以考虑', 'suggest', 'recommend', 'propose']

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in rec_keywords) and len(line) > 10:
                recommendations.append(line)

        return recommendations[:8]

    def _extract_key_points(self, text: str) -> List[str]:
        """提取关键点"""
        summarizer = DocumentSummarizer()

        sentences = summarizer._split_sentences(text)
        if sentences:
            sentences = [s for s in sentences if len(s) > 20]

        return sentences[:10] if len(sentences) > 10 else sentences

    def _generate_summary(self, text: str) -> str:
        """生成总结"""
        summarizer = DocumentSummarizer()
        sentences = summarizer._split_sentences(text)
        if sentences:
            sentences = [s for s in sentences if len(s) > 10]
            return ' '.join(sentences[:6])
        return text[:500]

    def _extract_main_points(self, text: str) -> List[str]:
        """提取主要观点"""
        summarizer = DocumentSummarizer()

        sentences = summarizer._split_sentences(text)
        scores = summarizer._score_sentences(sentences, text, 'zh')

        ranked_indices = sorted(range(len(scores)),
                              key=lambda i: scores[i],
                              reverse=True)[:8]
        ranked_indices.sort()

        return [sentences[i] for i in ranked_indices if i < len(sentences)]

    def _extract_meeting_title(self, text: str) -> str:
        """提取会议标题"""
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 150:
                line = re.sub(r'^[#会议纪要]+', '', line)
                return line
        return "会议纪要"