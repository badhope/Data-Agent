"""
任务二：NL2SQL引擎模块
实现自然语言到SQL的转换，包含意图分析、SQL生成、安全执行
"""
import re
import sqlite3
import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio


@dataclass
class SQLQuery:
    """SQL查询结果"""
    sql: str
    is_valid: bool
    explanation: str
    result: Optional[List[Dict]] = None
    error: Optional[str] = None


@dataclass
class IntentAnalysis:
    """意图分析结果"""
    intent_type: str  # "query", "trend", "comparison", "attribution", "prediction", "explanation"
    entities: Dict[str, Any]
    requires_clarification: bool
    clarification_questions: List[str]
    confidence: float


@dataclass
class TableSchema:
    """表结构定义"""
    table_name: str
    columns: List[Dict[str, str]]  # {name, type, description}
    primary_key: Optional[str] = None


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.schemas: Dict[str, TableSchema] = {}

    def create_financial_database(self):
        """创建财务数据库结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建公司基本信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT UNIQUE,
                company_name TEXT,
                industry TEXT,
                listing_date TEXT,
                stock_code TEXT
            )
        ''')
        
        # 创建财务指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT,
                report_type TEXT,  -- "annual", "quarterly", "semi-annual"
                year INTEGER,
                quarter INTEGER,
                revenue REAL,
                cost_of_goods_sold REAL,
                gross_profit REAL,
                operating_expenses REAL,
                operating_profit REAL,
                net_profit REAL,
                net_profit_attributable REAL,
                total_assets REAL,
                total_liabilities REAL,
                equity REAL,
                current_assets REAL,
                current_liabilities REAL,
                cash_from_operating REAL,
                cash_from_investing REAL,
                cash_from_financing REAL,
                FOREIGN KEY (company_code) REFERENCES companies(company_code)
            )
        ''')
        
        # 创建财务比率表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_ratios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT,
                year INTEGER,
                quarter INTEGER,
                gross_margin REAL,
                net_profit_margin REAL,
                roa REAL,
                roe REAL,
                debt_to_assets REAL,
                current_ratio REAL,
                quick_ratio REAL,
                FOREIGN KEY (company_code) REFERENCES companies(company_code)
            )
        ''')
        
        # 创建文档片段表（用于RAG）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE,
                company_code TEXT,
                report_type TEXT,
                year INTEGER,
                page_num INTEGER,
                content TEXT,
                embedding BLOB,
                FOREIGN KEY (company_code) REFERENCES companies(company_code)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 注册schema
        self._register_schemas()

    def _register_schemas(self):
        """注册表结构"""
        self.schemas['companies'] = TableSchema(
            table_name='companies',
            columns=[
                {'name': 'id', 'type': 'INTEGER', 'description': '主键'},
                {'name': 'company_code', 'type': 'TEXT', 'description': '公司代码'},
                {'name': 'company_name', 'type': 'TEXT', 'description': '公司名称'},
                {'name': 'industry', 'type': 'TEXT', 'description': '行业分类'},
                {'name': 'listing_date', 'type': 'TEXT', 'description': '上市日期'},
                {'name': 'stock_code', 'type': 'TEXT', 'description': '股票代码'}
            ],
            primary_key='id'
        )
        
        self.schemas['financial_metrics'] = TableSchema(
            table_name='financial_metrics',
            columns=[
                {'name': 'id', 'type': 'INTEGER', 'description': '主键'},
                {'name': 'company_code', 'type': 'TEXT', 'description': '公司代码'},
                {'name': 'report_type', 'type': 'TEXT', 'description': '报告类型'},
                {'name': 'year', 'type': 'INTEGER', 'description': '年份'},
                {'name': 'quarter', 'type': 'INTEGER', 'description': '季度'},
                {'name': 'revenue', 'type': 'REAL', 'description': '营业收入'},
                {'name': 'cost_of_goods_sold', 'type': 'REAL', 'description': '营业成本'},
                {'name': 'gross_profit', 'type': 'REAL', 'description': '毛利润'},
                {'name': 'operating_expenses', 'type': 'REAL', 'description': '运营费用'},
                {'name': 'operating_profit', 'type': 'REAL', 'description': '运营利润'},
                {'name': 'net_profit', 'type': 'REAL', 'description': '净利润'},
                {'name': 'net_profit_attributable', 'type': 'REAL', 'description': '归属于母公司净利润'},
                {'name': 'total_assets', 'type': 'REAL', 'description': '总资产'},
                {'name': 'total_liabilities', 'type': 'REAL', 'description': '总负债'},
                {'name': 'equity', 'type': 'REAL', 'description': '所有者权益'},
                {'name': 'current_assets', 'type': 'REAL', 'description': '流动资产'},
                {'name': 'current_liabilities', 'type': 'REAL', 'description': '流动负债'},
                {'name': 'cash_from_operating', 'type': 'REAL', 'description': '经营活动现金流'},
                {'name': 'cash_from_investing', 'type': 'REAL', 'description': '投资活动现金流'},
                {'name': 'cash_from_financing', 'type': 'REAL', 'description': '筹资活动现金流'}
            ],
            primary_key='id'
        )

    def insert_sample_data(self):
        """插入示例数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 插入示例公司
        sample_companies = [
            ('SH600519', '贵州茅台', '白酒', '2001-08-27', '600519'),
            ('SZ000001', '平安银行', '银行', '1991-04-03', '000001'),
            ('SH601318', '中国平安', '保险', '2007-03-01', '601318')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO companies 
            (company_code, company_name, industry, listing_date, stock_code)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_companies)
        
        # 插入示例财务数据
        sample_financials = [
            ('SH600519', 'annual', 2023, None, 1241.0, 300.0, 941.0, 150.0, 791.0, 750.0, 730.0, 
             3200.0, 800.0, 2400.0, 1800.0, 600.0, 500.0, -100.0, -200.0),
            ('SH600519', 'annual', 2022, None, 1100.0, 280.0, 820.0, 130.0, 690.0, 627.0, 610.0, 
             2800.0, 700.0, 2100.0, 1600.0, 550.0, 450.0, -80.0, -150.0)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO financial_metrics 
            (company_code, report_type, year, quarter, revenue, cost_of_goods_sold, 
             gross_profit, operating_expenses, operating_profit, net_profit, 
             net_profit_attributable, total_assets, total_liabilities, equity, 
             current_assets, current_liabilities, cash_from_operating, 
             cash_from_investing, cash_from_financing)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_financials)
        
        conn.commit()
        conn.close()

    def execute_query(self, sql: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """安全执行SQL查询"""
        # 安全检查：只允许SELECT语句
        if not sql.strip().upper().startswith('SELECT'):
            return False, [], "只允许SELECT查询语句"
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # 转换为字典
            results = []
            for row in rows:
                results.append(dict(row))
            
            conn.close()
            return True, results, None
            
        except Exception as e:
            return False, [], str(e)


class IntentAnalyzer:
    """意图分析器"""

    def __init__(self):
        self.intent_patterns = {
            'query': ['查询', '获取', '显示', '列出', 'find', 'get', 'show', 'list'],
            'trend': ['趋势', '增长', '下降', '变化', '趋势分析', 'trend', 'growth', 'increase', 'decrease'],
            'comparison': ['对比', '比较', '相比', '差异', 'compare', 'comparison', 'difference'],
            'attribution': ['原因', '归因', '为什么', 'why', 'reason', 'attribution'],
            'prediction': ['预测', '预计', '未来', 'prediction', 'forecast', 'predict'],
            'explanation': ['解释', '说明', '什么是', 'explain', 'what is']
        }
        
        self.entity_patterns = {
            'company': [r'贵州茅台', r'平安银行', r'中国平安', r'(\d{6})'],
            'year': [r'(\d{4})年?'],
            'metric': [r'营业收入|营收|净利润|总资产|净资产|现金流']
        }

    def analyze(self, query: str) -> IntentAnalysis:
        """分析用户查询意图"""
        intent_type = 'query'
        entities = {}
        requires_clarification = False
        clarification_questions = []
        
        # 简单的意图识别
        query_lower = query.lower()
        
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                intent_type = intent
                break
        
        # 简单的实体提取
        # 提取年份
        year_match = re.search(r'(\d{4})', query)
        if year_match:
            entities['year'] = int(year_match.group(1))
        
        # 提取公司
        for company in ['贵州茅台', '平安银行', '中国平安']:
            if company in query:
                entities['company'] = company
                break
        
        # 提取指标
        metrics = []
        for metric in ['营业收入', '净利润', '总资产', '净资产', '现金流']:
            if metric in query:
                metrics.append(metric)
        if metrics:
            entities['metrics'] = metrics
        
        # 检查是否需要澄清
        if 'company' not in entities and intent_type != 'explanation':
            requires_clarification = True
            clarification_questions.append("请问您想查询哪家公司的数据？")
        
        if 'year' not in entities and intent_type in ['query', 'trend', 'comparison']:
            requires_clarification = True
            clarification_questions.append("请问您想查询哪一年的数据？")
        
        return IntentAnalysis(
            intent_type=intent_type,
            entities=entities,
            requires_clarification=requires_clarification,
            clarification_questions=clarification_questions,
            confidence=0.75 if entities else 0.5
        )


class NL2SQLEngine:
    """NL2SQL引擎 - 将自然语言转换为SQL"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.intent_analyzer = IntentAnalyzer()

    async def generate_sql(self, query: str, schema_context: str = "") -> SQLQuery:
        """生成SQL查询"""
        # 步骤1：分析意图
        intent_analysis = self.intent_analyzer.analyze(query)
        
        if intent_analysis.requires_clarification:
            return SQLQuery(
                sql="",
                is_valid=False,
                explanation="需要用户澄清",
                error="; ".join(intent_analysis.clarification_questions)
            )
        
        # 步骤2：根据意图生成SQL（简化版，实际应该用LLM）
        sql = self._generate_sql_from_intent(intent_analysis, query)
        
        if not sql:
            return SQLQuery(
                sql="",
                is_valid=False,
                explanation="无法生成SQL查询",
                error="暂不支持该类型的查询"
            )
        
        # 步骤3：执行SQL
        success, results, error = self.db_manager.execute_query(sql)
        
        return SQLQuery(
            sql=sql,
            is_valid=success,
            explanation=results,
            result=results if success else None,
            error=error if not success else None
        )

    def _generate_sql_from_intent(self, intent_analysis: IntentAnalysis, query: str) -> str:
        """根据意图生成SQL（简化示例）"""
        entities = intent_analysis.entities
        
        company_code = None
        if 'company' in entities:
            company_map = {
                '贵州茅台': 'SH600519',
                '平安银行': 'SZ000001', 
                '中国平安': 'SH601318'
            }
            company_code = company_map.get(entities['company'])
        
        year = entities.get('year')
        metrics = entities.get('metrics', [])
        
        # 构建简单的查询
        if company_code:
            if year:
                base_sql = f"""
                    SELECT c.company_name, fm.year, fm.revenue, fm.net_profit, fm.total_assets
                    FROM financial_metrics fm
                    JOIN companies c ON fm.company_code = c.company_code
                    WHERE fm.company_code = '{company_code}' AND fm.year = {year}
                """
            else:
                base_sql = f"""
                    SELECT c.company_name, fm.year, fm.revenue, fm.net_profit, fm.total_assets
                    FROM financial_metrics fm
                    JOIN companies c ON fm.company_code = c.company_code
                    WHERE fm.company_code = '{company_code}'
                    ORDER BY fm.year DESC
                """
            return base_sql.strip()
        else:
            # 返回所有公司的财务数据
            return """
                SELECT c.company_name, fm.year, fm.revenue, fm.net_profit
                FROM financial_metrics fm
                JOIN companies c ON fm.company_code = c.company_code
                ORDER BY fm.year DESC
                LIMIT 10
            """.strip()

    def format_result(self, sql_query: SQLQuery) -> Dict[str, Any]:
        """格式化查询结果"""
        if not sql_query.is_valid:
            return {
                'success': False,
                'error': sql_query.error,
                'sql': sql_query.sql
            }
        
        return {
            'success': True,
            'sql': sql_query.sql,
            'result': sql_query.result,
            'count': len(sql_query.result) if sql_query.result else 0
        }


class FullNL2SQLPipeline:
    """完整的NL2SQL流水线"""

    def __init__(self, db_path: Path):
        self.db_manager = DatabaseManager(db_path)
        self.nl2sql_engine = NL2SQLEngine(self.db_manager)

    def initialize(self):
        """初始化数据库"""
        self.db_manager.create_financial_database()
        self.db_manager.insert_sample_data()

    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理用户查询"""
        # 步骤1：意图分析
        intent_analysis = self.nl2sql_engine.intent_analyzer.analyze(query)
        
        if intent_analysis.requires_clarification:
            return {
                'type': 'clarification',
                'intent': intent_analysis.intent_type,
                'questions': intent_analysis.clarification_questions
            }
        
        # 步骤2：生成SQL
        sql_query = await self.nl2sql_engine.generate_sql(query)
        
        # 步骤3：格式化结果
        result = self.nl2sql_engine.format_result(sql_query)
        
        return {
            'type': 'result',
            'intent': intent_analysis.intent_type,
            **result
        }
