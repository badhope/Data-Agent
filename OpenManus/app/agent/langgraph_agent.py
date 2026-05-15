"""LangGraph智能体框架集成 - 企业级多智能体编排"""
import asyncio
from typing import List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass

try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.tools import Tool
    from langchain_core.runnables import RunnableConfig
    from langchain_openai import ChatOpenAI
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

@dataclass
class AgentResult:
    """智能体执行结果"""
    success: bool
    content: str = ""
    tool_calls: List[Dict] = None
    error: str = ""
    thought: str = ""

class AgentState(TypedDict):
    """智能体状态"""
    messages: List[Any]
    summary: str
    tool_results: List[Dict]

class LangGraphAgent:
    """基于LangGraph的智能体实现"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.graph = None
        self.tools = []
        self.llm = None
        
        if LANGGRAPH_AVAILABLE:
            self._init_llm()
            self._build_graph()
    
    def _init_llm(self):
        """初始化LLM"""
        try:
            self.llm = ChatOpenAI(model=self.model_name, temperature=0)
        except Exception as e:
            print(f"初始化LLM失败: {e}")
    
    def _build_graph(self):
        """构建状态图"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("summarize", self._summarize_node)
        
        # 添加边
        workflow.add_edge("think", "act")
        workflow.add_edge("act", "summarize")
        workflow.add_edge("summarize", END)
        
        # 设置入口点
        workflow.set_entry_point("think")
        
        self.graph = workflow.compile()
    
    def _think_node(self, state: AgentState) -> AgentState:
        """思考节点 - 分析问题并决定下一步"""
        messages = state["messages"]
        
        # 调用LLM进行思考
        if self.llm:
            response = self.llm.invoke(messages)
            messages.append(response)
        
        return {
            "messages": messages,
            "summary": state.get("summary", ""),
            "tool_results": state.get("tool_results", [])
        }
    
    def _act_node(self, state: AgentState) -> AgentState:
        """行动节点 - 执行工具调用"""
        messages = state["messages"]
        tool_results = state.get("tool_results", [])
        
        # 检查是否需要调用工具
        last_message = messages[-1] if messages else None
        
        if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                result = self._execute_tool(tool_call)
                tool_results.append(result)
                messages.append(result)
        
        return {
            "messages": messages,
            "summary": state.get("summary", ""),
            "tool_results": tool_results
        }
    
    def _summarize_node(self, state: AgentState) -> AgentState:
        """总结节点 - 生成最终回复"""
        messages = state["messages"]
        
        # 生成总结
        if self.llm:
            summary_prompt = SystemMessage(content="请总结以上对话和工具执行结果，给出最终回复")
            response = self.llm.invoke([summary_prompt] + messages)
            messages.append(response)
        
        return {
            "messages": messages,
            "summary": response.content if 'response' in dir() else "",
            "tool_results": state.get("tool_results", [])
        }
    
    def _execute_tool(self, tool_call: Dict) -> AIMessage:
        """执行工具调用"""
        tool_name = tool_call.get("name")
        args = tool_call.get("args", {})
        
        # 查找并执行工具
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    result = tool.func(**args)
                    return AIMessage(
                        content=f"工具 {tool_name} 执行结果: {result}",
                        tool_calls=[],
                        tool_call_id=tool_call.get("id")
                    )
                except Exception as e:
                    return AIMessage(
                        content=f"工具 {tool_name} 执行失败: {str(e)}",
                        tool_calls=[],
                        tool_call_id=tool_call.get("id")
                    )
        
        return AIMessage(
            content=f"未找到工具: {tool_name}",
            tool_calls=[],
            tool_call_id=tool_call.get("id")
        )
    
    def add_tool(self, tool: Tool) -> None:
        """添加工具"""
        self.tools.append(tool)
    
    def add_tools(self, tools: List[Tool]) -> None:
        """批量添加工具"""
        self.tools.extend(tools)
    
    async def run(self, query: str, context: Optional[str] = None) -> AgentResult:
        """执行智能体"""
        if not LANGGRAPH_AVAILABLE:
            return AgentResult(
                success=False,
                error="LangGraph未安装，请安装: pip install langgraph langchain langchain-core"
            )
        
        if self.graph is None:
            return AgentResult(
                success=False,
                error="智能体图未构建"
            )
        
        try:
            # 构建初始消息
            messages = [HumanMessage(content=query)]
            if context:
                messages.insert(0, SystemMessage(content=context))
            
            # 执行图
            config = RunnableConfig()
            result = await self.graph.ainvoke({
                "messages": messages,
                "summary": "",
                "tool_results": []
            }, config)
            
            # 提取结果
            last_message = result["messages"][-1] if result["messages"] else None
            
            return AgentResult(
                success=True,
                content=last_message.content if last_message else "",
                tool_results=result.get("tool_results", []),
                summary=result.get("summary", "")
            )
        
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"执行失败: {str(e)}"
            )
    
    def run_sync(self, query: str, context: Optional[str] = None) -> AgentResult:
        """同步执行智能体"""
        return asyncio.run(self.run(query, context))
    
    @staticmethod
    def is_available() -> bool:
        """检查LangGraph是否可用"""
        return LANGGRAPH_AVAILABLE

# 全局实例
langgraph_agent = None

def get_langgraph_agent(model_name: str = "gpt-4o") -> LangGraphAgent:
    """获取全局LangGraph智能体实例"""
    global langgraph_agent
    if langgraph_agent is None:
        langgraph_agent = LangGraphAgent(model_name)
    return langgraph_agent