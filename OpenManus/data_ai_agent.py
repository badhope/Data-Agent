#!/usr/bin/env python3
"""
DATA-AI 万能智能助手
整合所有功能模块
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from web.modules.slideflow_module import SlideFlowAnalyzer, get_slideflow_module
    HAS_SLIDEFLOW = True
except:
    HAS_SLIDEFLOW = False

try:
    from web.modules.tools_module import DATA_AI_TOOLS, get_tools_module
    HAS_TOOLS = True
except:
    HAS_TOOLS = False
    print("⚠️  工具模块未加载")


@dataclass
class Capability:
    id: str
    name: str
    description: str
    icon: str
    category: str


class DATA_AI_AGENT:
    """DATA-AI 万能智能助手"""
    
    def __init__(self):
        self.name = "DATA-AI"
        self.version = "4.0.0"
        self.capabilities: List[Capability] = []
        self.slideflow = None
        self.tools = None
        
        self._init_capabilities()
        self._init_modules()
        
    def _init_capabilities(self):
        """初始化能力列表"""
        self.capabilities = [
            Capability("chat", "智能对话", "自然语言对话交互", "💬", "core"),
            Capability("code", "代码助手", "代码编写、调试、优化", "💻", "core"),
            Capability("data", "数据分析", "数据处理与可视化", "📊", "core"),
            Capability("document", "文档处理", "PDF解析、摘要、翻译", "📄", "core"),
            Capability("search", "信息检索", "网络搜索与信息聚合", "🔍", "core"),
            Capability("ppt", "PPT生成", "专业演示文稿生成", "📊", "tools"),
            Capability("chart", "图表可视化", "数据可视化图表生成", "📈", "tools"),
            Capability("sandbox", "代码沙盒", "安全代码执行环境", "🐍", "tools"),
            Capability("pathology", "病理分析", "SlideFlow 病理学分析", "🔬", "specialized"),
            Capability("skill", "技能系统", "自定义技能与工作流", "⚡", "system"),
            Capability("mcp", "MCP工具", "Model Context Protocol", "🔌", "system"),
        ]
    
    def _init_modules(self):
        """初始化功能模块"""
        if HAS_SLIDEFLOW:
            try:
                self.slideflow = get_slideflow_module()
                print("✅ SlideFlow 模块已加载")
            except Exception as e:
                print(f"❌ SlideFlow 初始化失败: {e}")
        
        if HAS_TOOLS:
            try:
                self.tools = get_tools_module()
                print("✅ 工具模块已加载")
            except Exception as e:
                print(f"❌ 工具模块初始化失败: {e}")
    
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
                    "icon": cap.icon,
                    "category": cap.category
                }
                for cap in self.capabilities
            ],
            "modules": {
                "slideflow": HAS_SLIDEFLOW and self.slideflow is not None,
                "tools": HAS_TOOLS and self.tools is not None,
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_request(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """处理用户请求"""
        context = context or {}
        user_input_lower = user_input.lower()
        
        if any(k in user_input_lower for k in ["ppt", "演示", "presentation", "幻灯片"]):
            return await self._handle_ppt(user_input, context)
        
        if any(k in user_input_lower for k in ["图表", "chart", "可视化", "graph", "图"]):
            return await self._handle_chart(user_input, context)
        
        if any(k in user_input_lower for k in ["沙盒", "sandbox", "执行", "run"]):
            return await self._handle_sandbox(user_input, context)
        
        if any(k in user_input_lower for k in ["病理", "切片", "slideflow", "wsi"]):
            return await self._handle_pathology(user_input, context)
        
        if any(k in user_input_lower for k in ["代码", "编程", "code", "python"]):
            return await self._handle_code(user_input, context)
        
        if any(k in user_input_lower for k in ["分析", "数据", "data"]):
            return await self._handle_data(user_input, context)
        
        if any(k in user_input_lower for k in ["文档", "pdf", "总结"]):
            return await self._handle_document(user_input, context)
        
        return await self._handle_chat(user_input, context)
    
    async def _handle_chat(self, user_input: str, context: Dict) -> Dict:
        """处理对话"""
        return {
            "type": "chat",
            "content": f"💬 收到消息：{user_input}\n\nDATA-AI 万能智能助手可以帮您：\n\n📊 **内容创作**\n- 智能对话\n- PPT 生成\n- 写作助手\n\n📈 **数据分析**\n- 数据可视化\n- 图表生成\n- 报告制作\n\n🐍 **代码开发**\n- 代码编写\n- 沙盒执行\n- 调试优化\n\n🔬 **专业分析**\n- 病理分析\n- 文档处理\n- 信息检索\n\n请告诉我您的需求！",
            "capability_used": "chat"
        }
    
    async def _handle_ppt(self, user_input: str, context: Dict) -> Dict:
        """处理 PPT 请求"""
        if not self.tools:
            return {"type": "ppt", "content": "⚠️ PPT 模块未加载", "capability_used": "ppt"}
        
        result = self.tools.ppt.generate_ppt(user_input)
        templates = "\n".join([f"- **{t['name']}**: {t['description']}" for t in self.tools.ppt.templates])
        
        return {
            "type": "ppt",
            "content": f"📊 **PPT 生成助手**\n\n主题：{result['topic']}\n模板：{result['template']}\n幻灯片数：{result['slides_count']}\n\n**可用模板：**\n{templates}\n\n请告诉我：\n1. 您的 PPT 主题\n2. 选择的模板类型\n3. 需要包含的内容",
            "capability_used": "ppt",
            "templates": self.tools.ppt.templates
        }
    
    async def _handle_chart(self, user_input: str, context: Dict) -> Dict:
        """处理图表请求"""
        if not self.tools:
            return {"type": "chart", "content": "⚠️ 图表模块未加载", "capability_used": "chart"}
        
        chart_types = "\n".join([f"- {c['icon']} **{c['name']}**: {c['description']}" for c in self.tools.chart.chart_types])
        
        return {
            "type": "chart",
            "content": f"📈 **图表可视化助手**\n\n支持的图表类型：\n{chart_types}\n\n**支持库：**\n{', '.join(self.tools.chart.libraries)}\n\n请告诉我：\n1. 数据内容或来源\n2. 需要的图表类型\n3. 图表标题",
            "capability_used": "chart",
            "chart_types": self.tools.chart.chart_types
        }
    
    async def _handle_sandbox(self, user_input: str, context: Dict) -> Dict:
        """处理沙盒请求"""
        if not self.tools:
            return {"type": "sandbox", "content": "⚠️ 沙盒模块未加载", "capability_used": "sandbox"}
        
        languages = "\n".join([f"- {l['icon']} **{l['name']}**: {l['description']}" for l in self.tools.sandbox.supported_languages])
        
        return {
            "type": "sandbox",
            "content": f"🐍 **代码沙盒助手**\n\n支持的编程语言：\n{languages}\n\n**安全模式：**\n- 🔒 安全模式：完全隔离\n- 📁 标准模式：允许基本文件\n- 💻 完整模式：完整权限\n\n请粘贴您的代码，我来帮您执行！",
            "capability_used": "sandbox",
            "languages": self.tools.sandbox.supported_languages
        }
    
    async def _handle_pathology(self, user_input: str, context: Dict) -> Dict:
        """处理病理分析"""
        if not self.slideflow:
            return {
                "type": "pathology",
                "content": "⚠️ SlideFlow 模块未加载\n\n请安装必要依赖：\n```bash\npip install numpy pillow slideflow\n```",
                "capability_used": "pathology"
            }
        
        analysis = self.slideflow.analyze_with_ai(user_input, context)
        return {
            "type": "pathology",
            "content": f"🔬 **SlideFlow 病理分析助手**\n\n{analysis['response']}",
            "capability_used": "pathology",
            "suggestions": analysis.get("suggestions", [])
        }
    
    async def _handle_code(self, user_input: str, context: Dict) -> Dict:
        """处理代码"""
        return {
            "type": "code",
            "content": "💻 **代码助手**\n\n我可以帮您：\n- 编写 Python、JavaScript、Java 等代码\n- 调试和修复错误\n- 优化代码性能\n- 在沙盒中执行代码\n\n请告诉我您的具体需求！",
            "capability_used": "code"
        }
    
    async def _handle_data(self, user_input: str, context: Dict) -> Dict:
        """处理数据"""
        return {
            "type": "data",
            "content": "📊 **数据分析助手**\n\n我可以帮您：\n- 数据清洗与预处理\n- 统计分析\n- 生成可视化图表\n- 趋势分析与预测\n\n支持：Pandas、Matplotlib、Seaborn、Plotly 等",
            "capability_used": "data"
        }
    
    async def _handle_document(self, user_input: str, context: Dict) -> Dict:
        """处理文档"""
        return {
            "type": "document",
            "content": "📄 **文档处理助手**\n\n我可以帮您：\n- PDF 解析与提取\n- 文档摘要生成\n- 多语言翻译\n- 关键信息提取\n\n支持格式：PDF、Word、TXT、Markdown 等",
            "capability_used": "document"
        }
    
    def get_tools_list(self) -> List[Dict]:
        """获取工具列表"""
        if self.tools:
            return self.tools.get_tools()
        return []


def create_agent() -> DATA_AI_AGENT:
    """创建 Agent"""
    return DATA_AI_AGENT()


async def main():
    """主函数"""
    print("=" * 60)
    print("🤖 DATA-AI 万能智能助手 v4.0")
    print("=" * 60)
    
    agent = create_agent()
    info = agent.get_system_info()
    
    print(f"\n✅ 版本: {info['version']}")
    print(f"✅ SlideFlow: {'已加载' if info['modules']['slideflow'] else '未加载'}")
    print(f"✅ 工具模块: {'已加载' if info['modules']['tools'] else '未加载'}")
    
    print(f"\n📋 核心能力 ({len(info['capabilities'])} 项):")
    for cap in info['capabilities']:
        print(f"  {cap['icon']} {cap['name']}: {cap['description']}")
    
    print("\n" + "=" * 60)
    return agent


if __name__ == "__main__":
    agent = asyncio.run(main())
