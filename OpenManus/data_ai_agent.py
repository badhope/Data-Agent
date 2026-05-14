#!/usr/bin/env python3
"""
DATA-AI 万能智能助手
整合 SlideFlow 病理学分析 + OpenManus Agent
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    from slideflow_module import SlideFlowAnalyzer, get_slideflow_module
    HAS_SLIDEFLOW = True
except ImportError:
    HAS_SLIDEFLOW = False
    print("⚠️  SlideFlow 模块未加载")

try:
    from agents import Agent
    from agents.tool import Tool
    HAS_OPENMANUS = True
except ImportError:
    HAS_OPENMANUS = False
    print("⚠️  OpenManus Agent 未加载")

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentCapability:
    id: str
    name: str
    description: str
    icon: str
    handler: callable


class DATA_AI_AGENT:
    """DATA-AI 万能智能助手"""
    
    def __init__(self):
        self.name = "DATA-AI"
        self.version = "3.0.0"
        self.capabilities: List[AgentCapability] = []
        self.slideflow: Optional[SlideFlowAnalyzer] = None
        
        self._init_capabilities()
        self._init_slideflow()
        
    def _init_capabilities(self):
        """初始化能力列表"""
        self.capabilities = [
            AgentCapability(
                id="chat",
                name="智能对话",
                description="自然语言对话交互",
                icon="💬",
                handler=self._handle_chat
            ),
            AgentCapability(
                id="code",
                name="代码助手",
                description="代码编写、调试、优化",
                icon="💻",
                handler=self._handle_code
            ),
            AgentCapability(
                id="data",
                name="数据分析",
                description="数据处理与可视化",
                icon="📊",
                handler=self._handle_data
            ),
            AgentCapability(
                id="document",
                name="文档处理",
                description="PDF解析、摘要、翻译",
                icon="📄",
                handler=self._handle_document
            ),
            AgentCapability(
                id="search",
                name="信息检索",
                description="网络搜索与信息聚合",
                icon="🔍",
                handler=self._handle_search
            ),
            AgentCapability(
                id="pathology",
                name="病理分析",
                description="SlideFlow 病理学图像分析",
                icon="🔬",
                handler=self._handle_pathology
            ),
            AgentCapability(
                id="skill",
                name="技能系统",
                description="自定义技能与工作流",
                icon="⚡",
                handler=self._handle_skill
            ),
            AgentCapability(
                id="mcp",
                name="MCP工具",
                description="Model Context Protocol 工具",
                icon="🔌",
                handler=self._handle_mcp
            ),
        ]
    
    def _init_slideflow(self):
        """初始化 SlideFlow 模块"""
        if HAS_SLIDEFLOW:
            try:
                self.slideflow = get_slideflow_module()
                print("✅ SlideFlow 模块已加载")
            except Exception as e:
                print(f"❌ SlideFlow 初始化失败: {e}")
                self.slideflow = None
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": [
                {
                    "id": cap.id,
                    "name": cap.name,
                    "description": cap.description,
                    "icon": cap.icon
                }
                for cap in self.capabilities
            ],
            "slideflow_loaded": HAS_SLIDEFLOW and self.slideflow is not None,
            "openmanus_loaded": HAS_OPENMANUS,
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_request(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """处理用户请求"""
        context = context or {}
        
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["病理", "切片", "slideflow", "wsi"]):
            return await self._handle_pathology(user_input, context)
        
        if any(keyword in user_input_lower for keyword in ["代码", "编程", "code", "python"]):
            return await self._handle_code(user_input, context)
        
        if any(keyword in user_input_lower for keyword in ["分析", "数据", "chart", "图表"]):
            return await self._handle_data(user_input, context)
        
        if any(keyword in user_input_lower for keyword in ["文档", "pdf", "总结", "翻译"]):
            return await self._handle_document(user_input, context)
        
        if any(keyword in user_input_lower for keyword in ["搜索", "查询", "search"]):
            return await self._handle_search(user_input, context)
        
        return await self._handle_chat(user_input, context)
    
    async def _handle_chat(self, user_input: str, context: Dict) -> Dict:
        """处理对话请求"""
        return {
            "type": "chat",
            "content": f"收到消息：{user_input}\n\n请问有什么可以帮助您的？",
            "capability_used": "chat",
            "suggestions": [
                "帮我写一段代码",
                "分析这份数据",
                "处理PDF文档",
                "搜索相关信息"
            ]
        }
    
    async def _handle_code(self, user_input: str, context: Dict) -> Dict:
        """处理代码请求"""
        return {
            "type": "code",
            "content": "💻 **代码助手已就绪**\n\n我可以帮您：\n- 编写 Python、JavaScript、Java 等代码\n- 调试和修复错误\n- 优化代码性能\n- 解释代码逻辑\n\n请告诉我您的具体需求！",
            "capability_used": "code",
            "examples": [
                "帮我写一个数据处理脚本",
                "优化这段代码的性能",
                "解释这个函数的逻辑"
            ]
        }
    
    async def _handle_data(self, user_input: str, context: Dict) -> Dict:
        """处理数据请求"""
        return {
            "type": "data",
            "content": "📊 **数据分析助手已就绪**\n\n我可以帮您：\n- 数据清洗与预处理\n- 统计分析\n- 可视化图表生成\n- 趋势分析与预测\n\n支持：Pandas、Matplotlib、Seaborn、Plotly 等库",
            "capability_used": "data",
            "examples": [
                "分析这份销售数据",
                "生成季度报告图表",
                "预测下季度趋势"
            ]
        }
    
    async def _handle_document(self, user_input: str, context: Dict) -> Dict:
        """处理文档请求"""
        return {
            "type": "document",
            "content": "📄 **文档处理助手已就绪**\n\n我可以帮您：\n- PDF 解析与提取\n- 文档摘要生成\n- 多语言翻译\n- 关键信息提取\n\n支持格式：PDF、Word、TXT、Markdown 等",
            "capability_used": "document",
            "examples": [
                "总结这份PDF文档",
                "翻译这段英文",
                "提取关键信息"
            ]
        }
    
    async def _handle_search(self, user_input: str, context: Dict) -> Dict:
        """处理搜索请求"""
        return {
            "type": "search",
            "content": "🔍 **信息检索助手已就绪**\n\n我可以帮您：\n- 全网深度搜索\n- 信息聚合整理\n- 来源验证\n- 摘要提取\n\n请告诉我您想搜索的内容！",
            "capability_used": "search",
            "examples": [
                "搜索最新的AI技术趋势",
                "查找相关文献资料",
                "收集行业报告"
            ]
        }
    
    async def _handle_pathology(self, user_input: str, context: Dict) -> Dict:
        """处理病理学分析请求"""
        if not HAS_SLIDEFLOW or self.slideflow is None:
            return {
                "type": "pathology",
                "content": "⚠️ SlideFlow 模块未加载\n\n请确保已安装必要的依赖：\n```bash\npip install numpy pillow\n```\n\n或使用完整版 SlideFlow：\n```bash\npip install slideflow\n```",
                "capability_used": "pathology",
                "slideflow_loaded": False
            }
        
        analysis = self.slideflow.analyze_with_ai(user_input, context)
        
        return {
            "type": "pathology",
            "content": f"🔬 **SlideFlow 病理学分析**\n\n{analysis['response']}",
            "capability_used": "pathology",
            "slideflow_loaded": True,
            "capabilities_used": analysis["capabilities_used"],
            "suggestions": analysis["suggestions"]
        }
    
    async def _handle_skill(self, user_input: str, context: Dict) -> Dict:
        """处理技能请求"""
        return {
            "type": "skill",
            "content": "⚡ **技能系统已就绪**\n\n我可以帮您：\n- 创建自定义技能\n- 配置工作流程\n- AI 辅助技能生成\n- 技能市场搜索\n\n请告诉我您想创建什么样的技能！",
            "capability_used": "skill"
        }
    
    async def _handle_mcp(self, user_input: str, context: Dict) -> Dict:
        """处理 MCP 工具请求"""
        return {
            "type": "mcp",
            "content": "🔌 **MCP 工具系统已就绪**\n\nModel Context Protocol 支持：\n- 文件系统工具\n- GitHub 集成\n- 数据库连接\n- 搜索工具\n- 自定义工具\n\n请告诉我您需要什么工具！",
            "capability_used": "mcp"
        }
    
    def get_slideflow_info(self) -> Dict:
        """获取 SlideFlow 模块信息"""
        if not HAS_SLIDEFLOW or self.slideflow is None:
            return {
                "loaded": False,
                "message": "SlideFlow 模块未加载"
            }
        
        caps = self.slideflow.get_capabilities()
        agent_config = self.slideflow.create_slideflow_agent()
        
        return {
            "loaded": True,
            "name": caps["name"],
            "capabilities": caps,
            "agent_config": agent_config
        }
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用工具"""
        tools = []
        
        for cap in self.capabilities:
            tools.append({
                "id": cap.id,
                "name": cap.name,
                "icon": cap.icon,
                "description": cap.description
            })
        
        if self.slideflow:
            sf_caps = self.slideflow.get_capabilities()
            for cap in sf_caps.get("capabilities", []):
                tools.append({
                    "id": f"sf_{cap['id']}",
                    "name": cap['name'],
                    "icon": "🔬",
                    "description": cap['description'],
                    "module": "slideflow"
                })
        
        return tools


def create_agent() -> DATA_AI_AGENT:
    """创建 DATA-AI Agent 实例"""
    return DATA_AI_AGENT()


async def main():
    """主函数"""
    print("=" * 60)
    print("🔬 DATA-AI 万能智能助手 (整合 SlideFlow)")
    print("=" * 60)
    
    agent = create_agent()
    info = agent.get_system_info()
    
    print(f"\n✅ 版本: {info['version']}")
    print(f"✅ SlideFlow: {'已加载' if info['slideflow_loaded'] else '未加载'}")
    print(f"✅ OpenManus: {'已加载' if info['openmanus_loaded'] else '未加载'}")
    
    print(f"\n📋 核心能力 ({len(info['capabilities'])} 项):")
    for cap in info['capabilities']:
        print(f"  {cap['icon']} {cap['name']}: {cap['description']}")
    
    if agent.slideflow:
        print("\n🔬 SlideFlow 病理学能力:")
        sf_info = agent.get_slideflow_info()
        for cap in sf_info['capabilities']['capabilities']:
            print(f"  - {cap['name']}: {cap['description']}")
    
    print("\n" + "=" * 60)
    print("💡 使用方法:")
    print("  agent = create_agent()")
    print("  result = await agent.process_request('您的请求')")
    print("=" * 60)
    
    return agent


if __name__ == "__main__":
    agent = asyncio.run(main())
