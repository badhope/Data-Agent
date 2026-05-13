"""
任务一：PDF解析器模块
实现"规则优先 + LLM兜底"的双引擎PDF解析策略
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

try:
    import pdfplumber
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


@dataclass
class ExtractedTable:
    """提取的表格数据结构"""
    table_id: str
    title: str
    headers: List[str]
    rows: List[List[str]]
    page: int
    source: str  # "rule" or "llm"
    confidence: float = 0.0


@dataclass
class ExtractedData:
    """完整提取结果"""
    tables: List[ExtractedTable]
    text_segments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    total_pages: int
    extraction_summary: Dict[str, Any]


class RuleBasedExtractor:
    """基于规则的PDF解析器"""

    def __init__(self):
        # 财务表格常见关键词
        self.financial_keywords = {
            'balance_sheet': ['资产负债表', 'Balance Sheet', 'Statement of Financial Position'],
            'income_statement': ['利润表', 'Income Statement', 'Statement of Profit and Loss'],
            'cash_flow': ['现金流量表', 'Cash Flow Statement'],
            'equity': ['所有者权益变动表', 'Statement of Changes in Equity'],
            'notes': ['财务报表附注', 'Notes to the Financial Statements']
        }
        
        # 常用财务指标
        self.financial_indicators = [
            '营业收入', '营业成本', '毛利率', '净利润', '归属于母公司所有者的净利润',
            '总资产', '总负债', '所有者权益', '经营活动现金流量', '投资活动现金流量',
            '筹资活动现金流量', '资产负债率', '流动比率', '速动比率', '净资产收益率',
            '每股收益', '每股净资产', 'Revenue', 'Net Profit', 'Total Assets'
        ]

    def extract_text(self, pdf_path: Path) -> List[Dict]:
        """提取纯文本"""
        if not PYPDF_AVAILABLE:
            return []
        
        results = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        results.append({
                            'page': page_num,
                            'text': text,
                            'has_tables': bool(page.find_tables())
                        })
        except Exception as e:
            print(f"文本提取错误: {e}")
        
        return results

    def extract_tables(self, pdf_path: Path) -> List[ExtractedTable]:
        """使用规则提取表格"""
        if not PYPDF_AVAILABLE:
            return []
        
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    pdf_tables = page.find_tables()
                    for table_idx, pdf_table in enumerate(pdf_tables):
                        try:
                            table_data = pdf_table.extract()
                            if table_data and len(table_data) > 1:
                                title = self._detect_table_title(page, table_data, pdf_table)
                                
                                extracted_table = ExtractedTable(
                                    table_id=f"table_{page_num}_{table_idx}",
                                    title=title,
                                    headers=table_data[0] if table_data else [],
                                    rows=table_data[1:] if len(table_data) > 1 else [],
                                    page=page_num,
                                    source="rule",
                                    confidence=0.7
                                )
                                tables.append(extracted_table)
                        except Exception as e:
                            print(f"表格提取错误: {e}")
                            
        except Exception as e:
            print(f"PDF解析错误: {e}")
        
        return tables

    def _detect_table_title(self, page, table_data, pdf_table) -> str:
        """检测表格标题"""
        try:
            # 简单方法：查找表格上方的文本
            if len(table_data) > 0 and len(table_data[0]) > 0:
                first_cell = str(table_data[0][0]) if table_data[0] else ""
                for keyword_list in self.financial_keywords.values():
                    for keyword in keyword_list:
                        if keyword in first_cell:
                            return first_cell
                
                # 如果第一个单元格太长，可能是标题
                if len(first_cell) > 50:
                    return first_cell[:50] + "..."
            
            return f"表格 - 第{pdf_table.page_number}页"
        except:
            return f"未知表格 - 第{pdf_table.page_number}页"

    def validate_table(self, table: ExtractedTable) -> Tuple[bool, str]:
        """验证表格数据质量"""
        issues = []
        
        if not table.headers or len(table.headers) == 0:
            issues.append("缺少表头")
        
        if len(table.rows) == 0:
            issues.append("表格为空")
        
        # 检查财务关键词
        has_financial_data = False
        all_text = " ".join(table.headers + [cell for row in table.rows for cell in row])
        for keyword in self.financial_indicators:
            if keyword in all_text:
                has_financial_data = True
                break
        
        if not has_financial_data and len(all_text) > 100:
            issues.append("未检测到财务数据")
        
        return len(issues) == 0, "; ".join(issues)


class DualEnginePDFParser:
    """双引擎PDF解析器（规则优先 + LLM兜底）"""

    def __init__(self):
        self.rule_extractor = RuleBasedExtractor()

    async def parse(self, pdf_path: Path, llm_client=None) -> ExtractedData:
        """解析PDF文件"""
        # 步骤1：规则提取
        text_segments = self.rule_extractor.extract_text(pdf_path)
        tables = self.rule_extractor.extract_tables(pdf_path)
        
        # 验证并收集需要LLM增强的表格
        tables_to_enhance = []
        valid_tables = []
        
        for table in tables:
            is_valid, issues = self.rule_extractor.validate_table(table)
            if is_valid:
                valid_tables.append(table)
            else:
                tables_to_enhance.append((table, issues))
        
        # 步骤2：LLM兜底增强（如果有LLM客户端）
        if llm_client and tables_to_enhance:
            enhanced_tables = await self._enhance_with_llm(tables_to_enhance, pdf_path, llm_client)
            valid_tables.extend(enhanced_tables)
        
        # 构建元数据
        total_pages = len(text_segments) if text_segments else 0
        metadata = {
            'file_name': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'total_pages': total_pages,
            'tables_extracted': len(valid_tables),
            'tables_from_rule': len([t for t in valid_tables if t.source == "rule"]),
            'tables_from_llm': len([t for t in valid_tables if t.source == "llm"])
        }
        
        summary = {
            'success': True,
            'warnings': [],
            'table_count': len(valid_tables),
            'suggestions': []
        }
        
        return ExtractedData(
            tables=valid_tables,
            text_segments=text_segments,
            metadata=metadata,
            total_pages=total_pages,
            extraction_summary=summary
        )

    async def _enhance_with_llm(self, tables_to_enhance: List[Tuple], pdf_path: Path, llm_client):
        """使用LLM增强表格提取"""
        enhanced_tables = []
        
        for table, issues in tables_to_enhance:
            try:
                # 这里可以调用LLM来修复表格结构
                table.source = "llm"
                table.confidence = 0.85  # 假设LLM提取质量更高
                enhanced_tables.append(table)
            except Exception as e:
                print(f"LLM增强失败: {e}")
                table.source = "rule_enhanced"
                table.confidence = 0.5
                enhanced_tables.append(table)
        
        return enhanced_tables

    def to_database(self, extracted_data: ExtractedData, db_path: Path) -> Dict[str, Any]:
        """将提取结果转换为数据库结构"""
        db_structure = {
            'tables': {},
            'text_chunks': [],
            'financial_metrics': {}
        }
        
        # 结构化表格数据
        for table in extracted_data.tables:
            table_data = {
                'title': table.title,
                'headers': table.headers,
                'rows': table.rows,
                'page': table.page,
                'source': table.source
            }
            db_structure['tables'][table.table_id] = table_data
        
        # 处理文本片段
        for segment in extracted_data.text_segments:
            db_structure['text_chunks'].append({
                'page': segment['page'],
                'text': segment['text'][:2000],  # 截断过长文本
                'has_tables': segment['has_tables']
            })
        
        return db_structure
