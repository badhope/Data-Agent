"""
泰迪杯B题完整功能模块
包含：
1. PDF解析器 (Task 1)
2. NL2SQL引擎 (Task 2)
3. RAG与向量数据库 (Task 3)
4. 意图识别与澄清
5. 多意图规划
6. 归因分析
7. 财务领域专门功能
"""
__version__ = "1.0.0"

from .pdf_parser import (
    DualEnginePDFParser,
    ExtractedTable,
    ExtractedData
)
from .nl2sql_engine import (
    FullNL2SQLPipeline,
    DatabaseManager,
    IntentAnalyzer,
    NL2SQLEngine
)
from .rag_and_planning import (
    FullTidyCupPipeline,
    RAGEngine,
    MultiIntentPlanner,
    AttributionAnalyzer,
    DocumentChunk,
    TaskPlan,
    AttributionResult
)

__all__ = [
    # PDF解析
    "DualEnginePDFParser",
    "ExtractedTable",
    "ExtractedData",
    # NL2SQL
    "FullNL2SQLPipeline",
    "DatabaseManager",
    "IntentAnalyzer",
    "NL2SQLEngine",
    # RAG与规划
    "FullTidyCupPipeline",
    "RAGEngine",
    "MultiIntentPlanner",
    "AttributionAnalyzer",
    "DocumentChunk",
    "TaskPlan",
    "AttributionResult"
]
