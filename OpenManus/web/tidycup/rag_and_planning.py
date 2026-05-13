"""
任务三：RAG模块、多意图规划和归因分析
实现向量存储、复合问题拆解、溯源功能
"""
import re
import json
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio


@dataclass
class DocumentChunk:
    """文档片段"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: Optional[float] = None


@dataclass
class SubTask:
    """子任务"""
    task_id: str
    task_type: str  # "query", "analysis", "visualization"
    description: str
    dependencies: List[str]
    query: str


@dataclass
class TaskPlan:
    """任务计划"""
    original_query: str
    sub_tasks: List[SubTask]
    execution_order: List[str]
    confidence: float


@dataclass
class AttributionSource:
    """归因来源"""
    source_type: str  # "document", "database", "knowledge_base"
    source_id: str
    snippet: str
    page_num: Optional[int] = None
    score: float = 0.0


@dataclass
class AttributionResult:
    """归因结果"""
    sources: List[AttributionSource]
    summary: str
    confidence: float


class SimpleVectorStore:
    """简单的向量存储（使用纯Python实现，避免复杂依赖）"""

    def __init__(self):
        self.chunks: Dict[str, DocumentChunk] = {}
        self.keyword_index: Dict[str, List[str]] = {}

    def add_chunk(self, chunk: DocumentChunk):
        """添加文档片段"""
        self.chunks[chunk.chunk_id] = chunk
        
        # 简单的关键词索引
        words = re.findall(r'[\w\u4e00-\u9fff]+', chunk.content.lower())
        for word in set(words):
            if word not in self.keyword_index:
                self.keyword_index[word] = []
            self.chunks[chunk.chunk_id] = chunk
            if chunk.chunk_id not in self.keyword_index[word]:
                self.keyword_index[word].append(chunk.chunk_id)

    def search(self, query: str, top_k: int = 5) -> List[DocumentChunk]:
        """简单的关键词搜索"""
        query_words = re.findall(r'[\w\u4e00-\u9fff]+', query.lower())
        
        # 计算匹配分数
        chunk_scores: Dict[str, int] = {}
        
        for word in query_words:
            if word in self.keyword_index:
                for chunk_id in self.keyword_index[word]:
                    chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + 1
        
        # 排序并返回
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        
        for chunk_id, score in sorted_chunks:
            chunk = self.chunks.get(chunk_id)
            if chunk:
                chunk.score = score / len(query_words) if query_words else 0.0
                results.append(chunk)
        
        return results


class RAGEngine:
    """RAG引擎 - 检索增强生成"""

    def __init__(self):
        self.vector_store = SimpleVectorStore()
        self.sample_documents = self._create_sample_documents()
        
        # 添加示例文档
        for doc in self.sample_documents:
            self.vector_store.add_chunk(doc)

    def _create_sample_documents(self) -> List[DocumentChunk]:
        """创建示例文档片段"""
        samples = [
            {
                "content": "贵州茅台2023年年度报告显示，公司实现营业收入1241亿元，同比增长17.3%。净利润750亿元，同比增长19.5%。主要产品飞天茅台酒销量持续增长。",
                "metadata": {"company": "贵州茅台", "year": 2023, "page": 5, "source": "annual_report"}
            },
            {
                "content": "2023年贵州茅台毛利率为75.8%，较上年略有提升。公司在产品结构优化和成本控制方面取得良好成效。核心产品高端白酒市场份额保持领先。",
                "metadata": {"company": "贵州茅台", "year": 2023, "page": 12, "source": "annual_report"}
            },
            {
                "content": "平安银行2023年实现营业收入1900亿元，净利润420亿元。零售业务持续增长，占比达到62%。资产质量保持稳定，不良率为1.02%。",
                "metadata": {"company": "平安银行", "year": 2023, "page": 7, "source": "annual_report"}
            },
            {
                "content": "中国平安2023年保险业务收入8000亿元，寿险业务平稳发展。科技业务贡献显著增长，金融科技子公司实现盈利。",
                "metadata": {"company": "中国平安", "year": 2023, "page": 3, "source": "annual_report"}
            },
            {
                "content": "白酒行业分析：2023年高端白酒市场持续扩容，消费升级趋势明显。贵州茅台、五粮液等龙头企业表现优异，市场集中度进一步提升。",
                "metadata": {"company": "行业分析", "year": 2023, "page": 1, "source": "industry_report"}
            }
        ]
        
        chunks = []
        for i, sample in enumerate(samples):
            chunk_id = f"chunk_{i}"
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                content=sample["content"],
                metadata=sample["metadata"]
            ))
        
        return chunks

    async def retrieve(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """检索相关文档"""
        results = self.vector_store.search(query, top_k)
        return results

    def build_context(self, chunks: List[DocumentChunk]) -> str:
        """构建上下文"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.metadata
            source_info = f"[来源{i}: {meta.get('company', '未知')} - {meta.get('year', '未知')}, 第{meta.get('page', 'N/A')}页]"
            context_parts.append(f"{source_info}\n{chunk.content}\n")
        
        return "\n".join(context_parts)


class MultiIntentPlanner:
    """多意图规划器 - 拆解复合问题"""

    def __init__(self):
        self.compound_patterns = [
            (r"(.+)和(.+)", "comparison"),
            (r"(.+)并(.+)", "sequence"),
            (r"(.+)然后(.+)", "sequence"),
            (r"(.+)的(.+)和(.+)的(.+)", "comparison")
        ]

    def plan(self, query: str) -> TaskPlan:
        """分析查询并创建任务计划"""
        sub_tasks = []
        execution_order = []
        
        # 简化的任务分解逻辑
        if "对比" in query or "比较" in query or "和" in query and "区别" in query:
            # 对比任务
            sub_tasks.append(SubTask(
                task_id="task1",
                task_type="query",
                description="获取第一个比较对象的数据",
                dependencies=[],
                query=self._extract_first_comparison(query)
            ))
            
            sub_tasks.append(SubTask(
                task_id="task2",
                task_type="query",
                description="获取第二个比较对象的数据",
                dependencies=[],
                query=self._extract_second_comparison(query)
            ))
            
            sub_tasks.append(SubTask(
                task_id="task3",
                task_type="analysis",
                description="对比分析数据差异",
                dependencies=["task1", "task2"],
                query="对比分析上述两个数据集的差异"
            ))
            
            execution_order = ["task1", "task2", "task3"]
        
        elif "趋势" in query or "增长" in query or "变化" in query:
            # 趋势分析任务
            sub_tasks.append(SubTask(
                task_id="task1",
                task_type="query",
                description="获取历史数据",
                dependencies=[],
                query=self._extract_year_query(query)
            ))
            
            sub_tasks.append(SubTask(
                task_id="task2",
                task_type="analysis",
                description="计算增长率和趋势",
                dependencies=["task1"],
                query="计算数据的年度增长率和趋势方向"
            ))
            
            sub_tasks.append(SubTask(
                task_id="task3",
                task_type="visualization",
                description="生成趋势图表",
                dependencies=["task1"],
                query="生成趋势可视化图表"
            ))
            
            execution_order = ["task1", "task2", "task3"]
        
        else:
            # 简单查询
            sub_tasks.append(SubTask(
                task_id="task1",
                task_type="query",
                description="执行主要查询",
                dependencies=[],
                query=query
            ))
            
            execution_order = ["task1"]
        
        return TaskPlan(
            original_query=query,
            sub_tasks=sub_tasks,
            execution_order=execution_order,
            confidence=0.7
        )

    def _extract_first_comparison(self, query: str) -> str:
        """提取第一个比较对象的查询（简化版）"""
        if "和" in query:
            parts = query.split("和")
            return parts[0]
        return query

    def _extract_second_comparison(self, query: str) -> str:
        """提取第二个比较对象的查询（简化版）"""
        if "和" in query:
            parts = query.split("和")
            if len(parts) > 1:
                return parts[1]
        return query

    def _extract_year_query(self, query: str) -> str:
        """提取年份查询"""
        return query


class AttributionAnalyzer:
    """归因分析器 - 追踪答案来源"""

    def __init__(self):
        pass

    async def analyze(self, query: str, rag_results: List[DocumentChunk], 
                     sql_result: Optional[Dict] = None) -> AttributionResult:
        """分析答案来源"""
        sources = []
        
        # 添加RAG检索结果作为来源
        for i, chunk in enumerate(rag_results):
            sources.append(AttributionSource(
                source_type="knowledge_base",
                source_id=chunk.chunk_id,
                snippet=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                page_num=chunk.metadata.get("page"),
                score=chunk.score or 0.0
            ))
        
        # 添加SQL结果作为来源
        if sql_result and sql_result.get("success"):
            sources.append(AttributionSource(
                source_type="database",
                source_id="sql_query",
                snippet=f"SQL查询结果: 共{sql_result.get('count', 0)}条记录",
                score=0.9
            ))
        
        # 生成归因摘要
        summary = self._generate_summary(sources)
        
        return AttributionResult(
            sources=sources,
            summary=summary,
            confidence=0.85 if sources else 0.0
        )

    def _generate_summary(self, sources: List[AttributionSource]) -> str:
        """生成归因摘要"""
        if not sources:
            return "未找到相关来源"
        
        kb_sources = [s for s in sources if s.source_type == "knowledge_base"]
        db_sources = [s for s in sources if s.source_type == "database"]
        
        parts = []
        if kb_sources:
            parts.append(f"参考了{len(kb_sources)}篇知识库文档")
        if db_sources:
            parts.append("查询了财务数据库")
        
        return "本答案基于: " + "、".join(parts)


class FullTidyCupPipeline:
    """完整的泰迪杯B题流水线"""

    def __init__(self, db_path: Path):
        from .nl2sql_engine import FullNL2SQLPipeline
        
        self.nl2sql_pipeline = FullNL2SQLPipeline(db_path)
        self.rag_engine = RAGEngine()
        self.planner = MultiIntentPlanner()
        self.attributor = AttributionAnalyzer()

    def initialize(self):
        """初始化所有模块"""
        self.nl2sql_pipeline.initialize()

    async def process_complex_query(self, query: str) -> Dict[str, Any]:
        """处理复杂查询"""
        # 步骤1：规划任务
        task_plan = self.planner.plan(query)
        
        # 步骤2：执行RAG检索
        rag_chunks = await self.rag_engine.retrieve(query)
        rag_context = self.rag_engine.build_context(rag_chunks)
        
        # 步骤3：执行NL2SQL（如果需要）
        sql_result = None
        if any(task.task_type == "query" for task in task_plan.sub_tasks):
            sql_result = await self.nl2sql_pipeline.process_query(query)
        
        # 步骤4：归因分析
        attribution = await self.attributor.analyze(query, rag_chunks, sql_result)
        
        # 构建最终结果
        result = {
            "original_query": query,
            "task_plan": {
                "sub_tasks": [
                    {
                        "id": t.task_id,
                        "type": t.task_type,
                        "description": t.description,
                        "query": t.query
                    } for t in task_plan.sub_tasks
                ],
                "execution_order": task_plan.execution_order
            },
            "rag_results": [
                {
                    "chunk_id": c.chunk_id,
                    "content": c.content,
                    "metadata": c.metadata,
                    "score": c.score
                } for c in rag_chunks
            ],
            "sql_result": sql_result,
            "attribution": {
                "sources": [
                    {
                        "type": s.source_type,
                        "id": s.source_id,
                        "snippet": s.snippet,
                        "score": s.score
                    } for s in attribution.sources
                ],
                "summary": attribution.summary
            }
        }
        
        return result
