"""文档加载器模块 - Document Loader Module"""
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod

class Document:
    """文档类"""

    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.metadata = metadata or {}
        self.chunks: List[str] = []

    def chunk(self, chunk_size: int = 512, overlap: int = 64) -> List[str]:
        """将文档分割成片段"""
        chunks = []
        text = self.content

        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)

        self.chunks = chunks
        return chunks

    def get_word_count(self) -> int:
        """获取词数"""
        return len(self.content.split())

    def get_char_count(self) -> int:
        """获取字符数"""
        return len(self.content)

class DocumentLoader(ABC):
    """文档加载器抽象基类"""

    @abstractmethod
    def load(self, path: str) -> Document:
        """加载文档"""
        pass

    @abstractmethod
    def supports(self, path: str) -> bool:
        """检查是否支持该文件类型"""
        pass

class TextLoader(DocumentLoader):
    """文本文件加载器"""

    def load(self, path: str) -> Document:
        """加载文本文件"""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        metadata = {
            'source': os.path.basename(path),
            'type': 'text',
            'size': os.path.getsize(path),
            'encoding': 'utf-8'
        }

        return Document(content, metadata)

    def supports(self, path: str) -> bool:
        """检查是否支持该文件类型"""
        ext = Path(path).suffix.lower()
        return ext in ['.txt', '.md', '.rst', '.json']

class MarkdownLoader(DocumentLoader):
    """Markdown文件加载器"""

    def load(self, path: str) -> Document:
        """加载Markdown文件"""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 提取基本元数据
        title = self._extract_title(content)

        metadata = {
            'source': os.path.basename(path),
            'type': 'markdown',
            'title': title,
            'size': os.path.getsize(path)
        }

        return Document(content, metadata)

    def _extract_title(self, content: str) -> str:
        """从Markdown提取标题"""
        lines = content.split('\n')
        for line in lines[:5]:
            if line.startswith('# '):
                return line[2:].strip()
        return ""

    def supports(self, path: str) -> bool:
        """检查是否支持该文件类型"""
        ext = Path(path).suffix.lower()
        return ext == '.md'

class HtmlLoader(DocumentLoader):
    """HTML文件加载器"""

    def load(self, path: str) -> Document:
        """加载HTML文件"""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 提取纯文本
        text = self._extract_text(content)

        metadata = {
            'source': os.path.basename(path),
            'type': 'html',
            'size': os.path.getsize(path)
        }

        return Document(text, metadata)

    def _extract_text(self, html: str) -> str:
        """从HTML提取纯文本"""
        # 移除脚本和样式
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

        # 移除标签
        text = re.sub(r'<[^>]+>', '', text)

        # 清理空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def supports(self, path: str) -> bool:
        """检查是否支持该文件类型"""
        ext = Path(path).suffix.lower()
        return ext in ['.html', '.htm']

class PDFLoader(DocumentLoader):
    """PDF文件加载器（简化版本）"""

    def __init__(self):
        self._pdfplumber_available = self._check_pdfplumber()

    def _check_pdfplumber(self) -> bool:
        """检查是否安装了pdfplumber"""
        try:
            import pdfplumber
            return True
        except ImportError:
            return False

    def load(self, path: str) -> Document:
        """加载PDF文件"""
        if self._pdfplumber_available:
            import pdfplumber
            content = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content += text + "\n\n"

            metadata = {
                'source': os.path.basename(path),
                'type': 'pdf',
                'pages': len(pdf.pages),
                'size': os.path.getsize(path)
            }
        else:
            # 回退到纯文本读取
            content = f"[PDF文件: {os.path.basename(path)} - 需要安装pdfplumber才能提取内容]"
            metadata = {
                'source': os.path.basename(path),
                'type': 'pdf',
                'size': os.path.getsize(path),
                'warning': 'pdfplumber未安装，无法提取内容'
            }

        return Document(content.strip(), metadata)

    def supports(self, path: str) -> bool:
        """检查是否支持该文件类型"""
        ext = Path(path).suffix.lower()
        return ext == '.pdf'

class DocumentLoaderFactory:
    """文档加载器工厂"""

    def __init__(self):
        self.loaders: List[DocumentLoader] = [
            MarkdownLoader(),
            TextLoader(),
            HtmlLoader(),
            PDFLoader()
        ]

    def get_loader(self, path: str) -> Optional[DocumentLoader]:
        """获取合适的加载器"""
        for loader in self.loaders:
            if loader.supports(path):
                return loader
        return None

    def load(self, path: str) -> Document:
        """加载文档"""
        loader = self.get_loader(path)
        if loader:
            return loader.load(path)

        # 默认加载为文本
        return TextLoader().load(path)

    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        extensions = []
        test_files = [
            'test.txt', 'test.md', 'test.html', 'test.pdf',
            'test.rst', 'test.json', 'test.htm'
        ]

        for file in test_files:
            if self.get_loader(file):
                extensions.append(Path(file).suffix)

        return extensions

class DirectoryLoader:
    """目录加载器"""

    def __init__(self, loader_factory: Optional[DocumentLoaderFactory] = None):
        self.loader_factory = loader_factory or DocumentLoaderFactory()

    def load_directory(self, dir_path: str, recursive: bool = True) -> List[Document]:
        """加载目录中的所有文档"""
        documents = []

        if not os.path.isdir(dir_path):
            return documents

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)

                try:
                    doc = self.loader_factory.load(file_path)
                    doc.metadata['path'] = file_path
                    documents.append(doc)
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {e}")

            if not recursive:
                break

        return documents

    def load_files(self, file_paths: List[str]) -> List[Document]:
        """加载多个文件"""
        documents = []

        for file_path in file_paths:
            if os.path.isfile(file_path):
                try:
                    doc = self.loader_factory.load(file_path)
                    doc.metadata['path'] = file_path
                    documents.append(doc)
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {e}")

        return documents