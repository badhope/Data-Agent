"""
PDF解析模块
支持PDF文档解析、文本提取和内容检索
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
import re
import io

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


@dataclass
class PDFPage:
    """PDF页面信息"""
    page_number: int
    text: str
    word_count: int
    char_count: int

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PDFMetadata:
    """PDF元数据"""
    title: str = ""
    author: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    modification_date: str = ""
    page_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PDFContent:
    """PDF内容"""
    metadata: PDFMetadata
    pages: List[PDFPage]
    full_text: str
    tables: List[List[List[str]]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'metadata': self.metadata.to_dict(),
            'page_count': len(self.pages),
            'total_word_count': sum(p.word_count for p in self.pages),
            'pages': [page.to_dict() for page in self.pages],
            'full_text': self.full_text,
            'tables': self.tables
        }


class PDFParser:
    """PDF解析器"""

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self):
        """检查依赖"""
        if pdfplumber is None:
            raise ImportError(
                "pdfplumber is not installed. Please install it with: pip install pdfplumber"
            )

    def parse_file(self, file_path: str, extract_tables: bool = False) -> PDFContent:
        """解析PDF文件"""
        with pdfplumber.open(file_path) as pdf:
            return self._parse_pdf(pdf, extract_tables)

    def parse_bytes(self, pdf_bytes: bytes, extract_tables: bool = False) -> PDFContent:
        """解析PDF字节流"""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return self._parse_pdf(pdf, extract_tables)

    def _parse_pdf(self, pdf, extract_tables: bool) -> PDFContent:
        """解析PDF对象"""
        metadata = self._extract_metadata(pdf)
        pages = []
        tables = []
        full_text_parts = []

        for page_num, page in enumerate(pdf.pages, 1):
            text = self._extract_text(page)
            full_text_parts.append(text)

            pages.append(PDFPage(
                page_number=page_num,
                text=text,
                word_count=self._count_words(text),
                char_count=len(text)
            ))

            if extract_tables:
                page_tables = self._extract_tables(page)
                if page_tables:
                    tables.extend(page_tables)

        return PDFContent(
            metadata=metadata,
            pages=pages,
            full_text='\n\n'.join(full_text_parts),
            tables=tables
        )

    def _extract_metadata(self, pdf) -> PDFMetadata:
        """提取元数据"""
        info = pdf.metadata or {}
        return PDFMetadata(
            title=info.get('Title', '').strip(),
            author=info.get('Author', '').strip(),
            creator=info.get('Creator', '').strip(),
            producer=info.get('Producer', '').strip(),
            creation_date=str(info.get('CreationDate', '')).strip(),
            modification_date=str(info.get('ModDate', '')).strip(),
            page_count=len(pdf.pages)
        )

    def _extract_text(self, page) -> str:
        """提取页面文本"""
        text = page.extract_text() or ""
        text = self._clean_text(text)
        return text

    def _extract_tables(self, page) -> List[List[List[str]]]:
        """提取表格"""
        tables = []
        try:
            page_tables = page.extract_tables()
            for table in page_tables:
                if table and len(table) > 0:
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [str(cell).strip() if cell else '' for cell in row]
                        if any(cell for cell in cleaned_row):
                            cleaned_table.append(cleaned_row)
                    if cleaned_table:
                        tables.append(cleaned_table)
        except Exception:
            pass
        return tables

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        text = text.replace('\r', '\n')
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(cleaned_lines)

    def _count_words(self, text: str) -> int:
        """统计单词数"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return chinese_chars + english_words

    def search_text(self, content: PDFContent, query: str, case_sensitive: bool = False) -> List[Dict]:
        """在PDF内容中搜索文本"""
        results = []
        search_text = query if case_sensitive else query.lower()

        for page in content.pages:
            page_text = page.text if case_sensitive else page.text.lower()
            if search_text in page_text:
                start_idx = page_text.find(search_text)
                context_before = page.text[max(0, start_idx - 50):start_idx]
                context_after = page.text[start_idx + len(query):start_idx + len(query) + 50]

                results.append({
                    'page_number': page.page_number,
                    'match': page.text[start_idx:start_idx + len(query)],
                    'context': f"...{context_before}{page.text[start_idx:start_idx + len(query)]}{context_after}..."
                })

        return results

    def extract_highlights(self, content: PDFContent) -> List[str]:
        """提取高亮内容（基于关键词分析）"""
        keywords = ['摘要', 'abstract', '结论', 'conclusion', '关键', '重要', '重点']
        highlights = []

        for page in content.pages:
            for keyword in keywords:
                if keyword in page.text:
                    sentences = page.text.split('。')
                    for sentence in sentences:
                        if keyword in sentence and len(sentence) > 10:
                            highlights.append(sentence.strip())

        return highlights[:10]


def parse_pdf(file_path: str, extract_tables: bool = False) -> Dict:
    """
    快速解析PDF文件的便捷函数

    Args:
        file_path: PDF文件路径
        extract_tables: 是否提取表格

    Returns:
        Dict: PDF内容字典
    """
    parser = PDFParser()
    content = parser.parse_file(file_path, extract_tables)
    return content.to_dict()


def parse_pdf_bytes(pdf_bytes: bytes, extract_tables: bool = False) -> Dict:
    """
    解析PDF字节流

    Args:
        pdf_bytes: PDF字节数据
        extract_tables: 是否提取表格

    Returns:
        Dict: PDF内容字典
    """
    parser = PDFParser()
    content = parser.parse_bytes(pdf_bytes, extract_tables)
    return content.to_dict()


def search_pdf_content(content: Dict, query: str) -> List[Dict]:
    """
    在PDF内容中搜索

    Args:
        content: PDF内容字典
        query: 搜索关键词

    Returns:
        List[Dict]: 搜索结果列表
    """
    parser = PDFParser()
    pages = [PDFPage(**page) for page in content.get('pages', [])]
    metadata = PDFMetadata(**content.get('metadata', {}))
    pdf_content = PDFContent(
        metadata=metadata,
        pages=pages,
        full_text=content.get('full_text', '')
    )
    return parser.search_text(pdf_content, query)
