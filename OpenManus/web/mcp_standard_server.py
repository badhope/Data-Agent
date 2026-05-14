"""
MCP Server - 标准的 Model Context Protocol 服务器实现
使用 Anthropic 的 FastMCP 框架
"""
from typing import Dict, Any, Optional
from pathlib import Path


# ==================== MCP 服务器框架检查 ====================

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None


# ==================== MCP 服务器配置 ====================

if MCP_AVAILABLE:
    # 初始化 MCP 服务器
    mcp = FastMCP("data_ai_mcp")
    
    # ==================== MCP 工具 ====================
    
    @mcp.tool()
    async def query_financial_data(
        company: str,
        year: Optional[int] = None,
        metric: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询财务数据
        
        Args:
            company: 公司名称
            year: 可选年份
            metric: 可选指标 (revenue, profit, assets, etc.)
            
        Returns:
            财务数据结果
        """
        try:
            from web.tidycup.nl2sql_engine import FullNL2SQLPipeline
            db_path = Path.cwd() / "data" / "mcp_server.db"
            pipeline = FullNL2SQLPipeline(db_path)
            pipeline.initialize()
            
            result = await pipeline.process_query(
                query=f"{company} {year or ''} {metric or ''}"
            )
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def generate_skill(
        skill_type: str,
        description: str,
        parameters: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成新技能
        
        Args:
            skill_type: 技能类型 (data_analysis, code_execution, document_processing)
            description: 技能描述
            parameters: JSON 格式的参数配置
            
        Returns:
            生成的技能配置
        """
        try:
            from web.skill_manager import generate_ai_skill
            import json
            
            param_list = json.loads(parameters) if parameters else None
            result = await generate_ai_skill(skill_type, description, param_list)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def execute_skill(
        skill_id: str,
        params: Optional[str] = "{}"
    ) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill_id: 技能ID
            params: JSON 格式的参数
            
        Returns:
            执行结果
        """
        try:
            from web.skill_manager import execute_skill
            import json
            
            param_dict = json.loads(params)
            result = await execute_skill(skill_id, param_dict)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== MCP 资源 ====================
    
    @mcp.resource("knowledge://sample/company/maotai")
    def get_maotai_financials() -> str:
        """获取茅台财务知识"""
        return """
        # 贵州茅台财务概况
        
        公司名称: 贵州茅台酒股份有限公司
        股票代码: 600519.SH
        行业: 白酒制造
        
        2023年关键财务指标:
        - 营业收入: 1,413.9亿元
        - 净利润: 748.5亿元
        - 总资产: 2,503.8亿元
        - 净资产收益率: 34.6%
        """
    
    @mcp.resource("knowledge://sample/company/pingan")
    def get_pingan_financials() -> str:
        """获取平安财务知识"""
        return """
        # 中国平安保险财务概况
        
        公司名称: 中国平安保险(集团)股份有限公司
        股票代码: 601318.SH
        行业: 保险
        
        2023年关键财务指标:
        - 营业收入: 10,716.2亿元
        - 净利润: 1,074.0亿元
        - 总资产: 11.9万亿元
        - 净资产收益率: 12.8%
        """
    
    # ==================== MCP 提示模板 ====================
    
    @mcp.prompt()
    def financial_analysis_prompt(company: str, year: int) -> str:
        """生成财务分析提示"""
        return f"""
        请对 {company} {year} 年的财务数据进行全面分析，包括:
        1. 营收和利润趋势
        2. 资产负债状况
        3. 现金流量分析
        4. 关键财务指标
        5. 与行业的对比
        """
    
    @mcp.prompt()
    def code_review_prompt(code: str, language: str = "python") -> str:
        """生成代码审查提示"""
        return f"""
        请审查以下{language}代码，重点关注:
        1. 语法错误
        2. 潜在的bug
        3. 性能优化空间
        4. 代码风格
        5. 安全问题
        
        代码:
        ```{language}
        {code}
        ```
        """


# ==================== 服务器启动函数 ====================

def run_mcp_server():
    """启动 MCP 服务器"""
    if not MCP_AVAILABLE:
        print("Error: mcp Python package not installed")
        print("Install with: pip install mcp")
        return
    
    print("Starting DATA-AI MCP Server...")
    print("Server: data_ai_mcp")
    print("Tools: query_financial_data, generate_skill, execute_skill")
    print("Resources: knowledge://sample/company/*")
    print("-" * 50)
    
    mcp.run()


if __name__ == "__main__":
    run_mcp_server()
