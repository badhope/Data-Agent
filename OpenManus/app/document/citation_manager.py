"""
引用管理模块
管理和格式化参考文献
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re
import json


@dataclass
class Citation:
    """引用文献"""
    citation_id: str = ""
    authors: List[str] = field(default_factory=list)
    title: str = ""
    year: str = ""
    source: str = ""
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    citation_type: str = "article"

    def to_dict(self) -> Dict:
        return {
            'citation_id': self.citation_id,
            'authors': self.authors,
            'title': self.title,
            'year': self.year,
            'source': self.source,
            'volume': self.volume,
            'issue': self.issue,
            'pages': self.pages,
            'doi': self.doi,
            'url': self.url,
            'publisher': self.publisher,
            'citation_type': self.citation_type
        }


class CitationManager:
    """引用管理器"""

    def __init__(self):
        self.citations: List[Citation] = []
        self.next_id = 1

    def add_citation(self, citation: Citation) -> str:
        """添加引用"""
        if not citation.citation_id:
            citation.citation_id = f"ref_{self.next_id}"
            self.next_id += 1

        self.citations.append(citation)
        return citation.citation_id

    def add_from_text(self, text: str) -> int:
        """从文本解析添加引用"""
        lines = text.split('\n')
        added_count = 0

        for line in lines:
            line = line.strip()
            if len(line) > 20:
                citation = self._parse_citation_line(line)
                if citation and citation.title:
                    self.add_citation(citation)
                    added_count += 1

        return added_count

    def add_from_dict(self, citation_data: Dict) -> str:
        """从字典添加引用"""
        citation = Citation(**citation_data)
        return self.add_citation(citation)

    def _parse_citation_line(self, line: str) -> Optional[Citation]:
        """解析引用行"""
        citation = Citation()

        year_match = re.search(r'\((\d{4})\)|\b(19|20)\d{2}\b', line)
        if year_match:
            citation.year = year_match.group(1) or year_match.group(2)

        author_pattern = r'^([A-Za-z][a-z]+(?:,\s*[A-Z][a-z]*\.?)*)'
        author_match = re.match(author_pattern, line)
        if author_match:
            author_str = author_match.group(1)
            citation.authors = [a.strip().rstrip('.') for a in author_str.split(',')]

        title_match = re.search(r'《(.+?)》|"(.+?)"|"(.+?)"|\'(.+?)\'|([A-Z][^,.]+?)\.', line)
        if title_match:
            citation.title = title_match.group(1) or title_match.group(2) or title_match.group(3) or title_match.group(4) or title_match.group(5)
        else:
            parts = re.split(r'[\.,]\s*', line)
            if len(parts) > 1:
                citation.title = parts[1].strip()[:100]

        doi_match = re.search(r'doi[:：]?\s*(10\.\S+)', line, re.IGNORECASE)
        if doi_match:
            citation.doi = doi_match.group(1)

        url_match = re.search(r'https?://\S+', line)
        if url_match:
            citation.url = url_match.group(0)

        if '[' in line and ']' in line:
            type_match = re.search(r'\[(\w+)\]', line)
            if type_match:
                citation.citation_type = self._determine_type(type_match.group(1))

        return citation

    def _determine_type(self, type_str: str) -> str:
        """确定引用类型"""
        type_map = {
            'J': 'article',
            'A': 'article',
            'M': 'book',
            'B': 'book',
            'C': 'conference',
            'N': 'newspaper',
            'D': 'thesis',
            'R': 'report',
            'S': 'standard',
            'P': 'patent',
        }
        return type_map.get(type_str.upper(), 'article')

    def format_bibliography(self, style: str = "gbt") -> str:
        """格式化参考文献"""
        if style == "apa":
            return self._format_apa()
        elif style == "mla":
            return self._format_mla()
        elif style == "chicago":
            return self._format_chicago()
        elif style == "gbt":
            return self._format_gbt7714()
        else:
            return self._format_simple()

    def _format_authors_apa(self, authors: List[str]) -> str:
        """格式化作者（APA）"""
        if not authors:
            return "Anonymous"
        if len(authors) == 1:
            return authors[0]
        if len(authors) == 2:
            return f"{authors[0]}, & {authors[1]}"
        if len(authors) <= 7:
            return ", ".join(authors[:-1]) + f", & {authors[-1]}"
        return ", ".join(authors[:6]) + f", ... {authors[-1]}"

    def _format_apa(self) -> str:
        """APA格式"""
        references = []

        for i, cite in enumerate(self.citations, 1):
            parts = []

            authors = self._format_authors_apa(cite.authors)
            if authors:
                parts.append(authors)

            if cite.year:
                parts.append(f"({cite.year})")

            if cite.title:
                parts.append(cite.title + ".")

            if cite.source:
                source_text = f"*{cite.source}*"
                if cite.volume:
                    source_text += f", {cite.volume}"
                if cite.issue:
                    source_text += f"({cite.issue})"
                if cite.pages:
                    source_text += f", {cite.pages}"
                source_text += "."
                parts.append(source_text)

            if cite.doi:
                parts.append(f"https://doi.org/{cite.doi}")

            references.append(" ".join(parts))

        return "\n\n".join([f"{i}. {ref}" for i, ref in enumerate(references, 1)])

    def _format_mla(self) -> str:
        """MLA格式"""
        references = []

        for cite in self.citations:
            parts = []

            if cite.authors:
                parts.append(", ".join(cite.authors) + ".")

            if cite.title:
                parts.append(f'"{cite.title}."')

            if cite.source:
                parts.append(f"*{cite.source}*, ")

            if cite.volume:
                parts.append(f"vol. {cite.volume}, ")

            if cite.issue:
                parts.append(f"no. {cite.issue}, ")

            if cite.year:
                parts.append(f"{cite.year}, ")

            if cite.pages:
                parts.append(f"pp. {cite.pages}.")

            reference = " ".join(parts)
            reference = re.sub(r',\s*\.$', '.', reference)
            references.append(reference)

        return "\n\n".join(references)

    def _format_chicago(self) -> str:
        """Chicago格式"""
        references = []

        for cite in self.citations:
            parts = []

            if cite.authors:
                parts.append(", ".join(cite.authors) + ".")

            if cite.title:
                parts.append(f'"{cite.title}."')

            if cite.source:
                parts.append(f"*{cite.source}*")

            if cite.volume:
                parts.append(f"{cite.volume}")

            if cite.issue:
                parts.append(f", no. {cite.issue}")

            if cite.year:
                parts.append(f" ({cite.year})")

            if cite.pages:
                parts.append(f": {cite.pages}")

            parts.append(".")

            if cite.doi:
                parts.append(f" https://doi.org/{cite.doi}.")

            references.append("".join(parts))

        return "\n\n".join(references)

    def _format_gbt7714(self) -> str:
        """GB/T 7714格式（中国国家标准）"""
        references = []

        for cite in self.citations:
            parts = []

            if cite.authors:
                authors_str = " ".join(cite.authors)
                parts.append(authors_str + ".")

            if cite.title:
                parts.append(cite.title + ".")

            if cite.source:
                parts.append(cite.source)

                if cite.volume:
                    parts[-1] += f", {cite.volume}"

                if cite.issue:
                    parts[-1] += f"({cite.issue})"

                if cite.pages:
                    parts[-1] += f": {cite.pages}"

                parts[-1] += "."

            if cite.year:
                parts.append(cite.year + ".")

            if cite.doi:
                parts.append(f"DOI: {cite.doi}")

            references.append("".join(parts))

        return "\n\n".join(references)

    def _format_simple(self) -> str:
        """简化格式"""
        references = []

        for i, cite in enumerate(self.citations, 1):
            author_str = ", ".join(cite.authors[:3]) if cite.authors else "Unknown"
            ref = f"[{i}] {cite.title} - {author_str}, {cite.year}"
            references.append(ref)

        return "\n".join(references)

    def format_citation(self, citation_id: str, style: str = "apa") -> str:
        """格式化单个引用"""
        for cite in self.citations:
            if cite.citation_id == citation_id:
                return self._format_single_citation(cite, style)
        return ""

    def _format_single_citation(self, citation: Citation, style: str) -> str:
        """格式化单个引用"""
        if style == "apa":
            authors = self._format_authors_apa(citation.authors)
            parts = [f"{authors} ({citation.year}). {citation.title}."]
            if citation.source:
                source = citation.source
                if citation.volume:
                    source += f", {citation.volume}"
                if citation.issue:
                    source += f"({citation.issue})"
                if citation.pages:
                    source += f", {citation.pages}"
                parts.append(f"*{source}*.")
            if citation.doi:
                parts.append(f"https://doi.org/{citation.doi}")
            return " ".join(parts)
        else:
            author_str = ", ".join(citation.authors) if citation.authors else ""
            return f"{author_str}. {citation.title}. {citation.year}."

    def in_text_citation(self, citation_id: str, style: str = "apa") -> str:
        """生成文中引用"""
        for cite in self.citations:
            if cite.citation_id == citation_id:
                if style == "apa":
                    if cite.authors:
                        if len(cite.authors) == 1:
                            return f"({cite.authors[0]}, {cite.year})"
                        elif len(cite.authors) == 2:
                            return f"({cite.authors[0]} & {cite.authors[1]}, {cite.year})"
                        else:
                            return f"({cite.authors[0]} et al., {cite.year})"
                    return f"(Anonymous, {cite.year})"
                else:
                    return f"[{citation_id}]"
        return ""

    def get_citation_count(self) -> int:
        """获取引用数量"""
        return len(self.citations)

    def export_json(self) -> str:
        """导出为JSON"""
        data = [cite.to_dict() for cite in self.citations]
        return json.dumps(data, ensure_ascii=False, indent=2)

    def import_json(self, json_str: str) -> int:
        """从JSON导入"""
        try:
            data = json.loads(json_str)
            imported = 0
            for item in data:
                citation = Citation(**item)
                self.add_citation(citation)
                imported += 1
            return imported
        except Exception:
            return 0

    def remove_citation(self, citation_id: str) -> bool:
        """删除引用"""
        for i, cite in enumerate(self.citations):
            if cite.citation_id == citation_id:
                self.citations.pop(i)
                return True
        return False

    def get_citation_by_id(self, citation_id: str) -> Optional[Citation]:
        """根据ID获取引用"""
        for cite in self.citations:
            if cite.citation_id == citation_id:
                return cite
        return None

    def search_citations(self, query: str) -> List[Citation]:
        """搜索引用"""
        results = []
        query_lower = query.lower()

        for cite in self.citations:
            if (query_lower in cite.title.lower() or
                any(query_lower in author.lower() for author in cite.authors) or
                query_lower in cite.source.lower() or
                query_lower in cite.year):
                results.append(cite)

        return results

    def get_statistics(self) -> Dict:
        """获取引用统计"""
        total = len(self.citations)

        by_type = {}
        by_year = {}

        for cite in self.citations:
            by_type[cite.citation_type] = by_type.get(cite.citation_type, 0) + 1

            if cite.year:
                by_year[cite.year] = by_year.get(cite.year, 0) + 1

        return {
            'total': total,
            'by_type': by_type,
            'by_year': by_year
        }


def format_citation(text: str, style: str = "gbt") -> str:
    """格式化引用的便捷函数"""
    manager = CitationManager()
    manager.add_from_text(text)
    return manager.format_bibliography(style)
