"""PyMuPDF文档处理器 - 使用PyMuPDF实现高性能PDF处理"""
import os
import io
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

@dataclass
class PDFPage:
    """PDF页面信息"""
    page_number: int
    text: str
    images: List[str] = None
    tables: List[List[List[str]]] = None

@dataclass
class PDFResult:
    """PDF处理结果"""
    success: bool
    text: str = ""
    pages: List[PDFPage] = None
    metadata: Dict[str, Any] = None
    error: str = ""
    page_count: int = 0
    word_count: int = 0

class PyMuPDFProcessor:
    """PyMuPDF文档处理器"""
    
    def __init__(self):
        if not PYMUPDF_AVAILABLE:
            print("警告: PyMuPDF未安装，某些功能可能受限")
    
    def extract_text(self, file_path: str) -> PDFResult:
        """
        提取PDF文本内容
        
        Args:
            file_path: PDF文件路径
        
        Returns:
            PDFResult: 处理结果
        """
        if not PYMUPDF_AVAILABLE:
            return PDFResult(
                success=False,
                error="PyMuPDF未安装，请安装: pip install pymupdf"
            )
        
        try:
            doc = fitz.open(file_path)
            
            pages = []
            full_text = ""
            word_count = 0
            
            for page_num, page in enumerate(doc, 1):
                # 提取文本
                text = page.get_text()
                full_text += text + "\n\n"
                word_count += len(text.split())
                
                # 提取图片
                images = []
                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    if base_image:
                        images.append(base_image.get("ext", "png"))
                
                pages.append(PDFPage(
                    page_number=page_num,
                    text=text,
                    images=images,
                    tables=self._extract_tables(page)
                ))
            
            # 获取元数据
            metadata = self._get_metadata(doc)
            
            doc.close()
            
            return PDFResult(
                success=True,
                text=full_text.strip(),
                pages=pages,
                metadata=metadata,
                page_count=len(pages),
                word_count=word_count
            )
        
        except Exception as e:
            return PDFResult(
                success=False,
                error=f"处理PDF失败: {str(e)}"
            )
    
    def _extract_tables(self, page) -> List[List[List[str]]]:
        """从页面提取表格（简化实现）"""
        tables = []
        try:
            # 使用文本块分析识别表格
            text_blocks = page.get_text("blocks")
            if text_blocks:
                # 简单的表格检测逻辑
                tables.append([["表格内容需要进一步解析"]])
        except Exception:
            pass
        
        return tables if tables else None
    
    def _get_metadata(self, doc) -> Dict[str, Any]:
        """获取文档元数据"""
        metadata = {}
        try:
            info = doc.metadata
            metadata = {
                'title': info.get('title', ''),
                'author': info.get('author', ''),
                'subject': info.get('subject', ''),
                'keywords': info.get('keywords', ''),
                'creator': info.get('creator', ''),
                'producer': info.get('producer', ''),
                'creation_date': info.get('creationDate', ''),
                'modification_date': info.get('modDate', '')
            }
        except Exception:
            pass
        
        return metadata
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> PDFResult:
        """
        从字节数据提取PDF文本
        
        Args:
            pdf_bytes: PDF字节数据
        
        Returns:
            PDFResult: 处理结果
        """
        if not PYMUPDF_AVAILABLE:
            return PDFResult(
                success=False,
                error="PyMuPDF未安装"
            )
        
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            pages = []
            full_text = ""
            word_count = 0
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                full_text += text + "\n\n"
                word_count += len(text.split())
                
                pages.append(PDFPage(
                    page_number=page_num,
                    text=text,
                    images=[],
                    tables=None
                ))
            
            metadata = self._get_metadata(doc)
            doc.close()
            
            return PDFResult(
                success=True,
                text=full_text.strip(),
                pages=pages,
                metadata=metadata,
                page_count=len(pages),
                word_count=word_count
            )
        
        except Exception as e:
            return PDFResult(
                success=False,
                error=f"处理PDF失败: {str(e)}"
            )
    
    def extract_page_text(self, file_path: str, page_number: int) -> Optional[str]:
        """
        提取指定页面的文本
        
        Args:
            file_path: PDF文件路径
            page_number: 页码（从1开始）
        
        Returns:
            str: 页面文本，失败返回None
        """
        if not PYMUPDF_AVAILABLE:
            return None
        
        try:
            doc = fitz.open(file_path)
            
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return None
            
            page = doc[page_number - 1]
            text = page.get_text()
            
            doc.close()
            return text
        
        except Exception:
            return None
    
    def extract_images(self, file_path: str, output_dir: str = "./images") -> List[str]:
        """
        提取PDF中的图片
        
        Args:
            file_path: PDF文件路径
            output_dir: 输出目录
        
        Returns:
            List[str]: 保存的图片路径列表
        """
        if not PYMUPDF_AVAILABLE:
            return []
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            doc = fitz.open(file_path)
            
            saved_paths = []
            
            for page_num, page in enumerate(doc, 1):
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        img_bytes = base_image["image"]
                        img_ext = base_image["ext"]
                        img_path = os.path.join(output_dir, f"page_{page_num}_img_{img_index}.{img_ext}")
                        
                        with open(img_path, 'wb') as f:
                            f.write(img_bytes)
                        
                        saved_paths.append(img_path)
            
            doc.close()
            return saved_paths
        
        except Exception:
            return []
    
    def get_page_count(self, file_path: str) -> int:
        """获取PDF页数"""
        if not PYMUPDF_AVAILABLE:
            return 0
        
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0
    
    def is_pdf_encrypted(self, file_path: str) -> bool:
        """检查PDF是否加密"""
        if not PYMUPDF_AVAILABLE:
            return False
        
        try:
            doc = fitz.open(file_path)
            encrypted = doc.needs_pass
            doc.close()
            return encrypted
        except Exception:
            return False
    
    @staticmethod
    def is_available() -> bool:
        """检查PyMuPDF是否可用"""
        return PYMUPDF_AVAILABLE
    
    @staticmethod
    def supports_file(file_path: str) -> bool:
        """检查是否支持该文件类型"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.pdf']

# 全局实例
pdf_processor = None

def get_pdf_processor() -> PyMuPDFProcessor:
    """获取全局PDF处理器实例"""
    global pdf_processor
    if pdf_processor is None:
        pdf_processor = PyMuPDFProcessor()
    return pdf_processor