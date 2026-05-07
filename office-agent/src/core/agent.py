"""
LangChain Office Agent Core Module
核心 Agent 实现，基于 LangChain 的 ReAct 架构
"""

from typing import List, Optional, Dict, Any, Callable
from langchain_core.tools import Tool, BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from .config import OfficeAgentConfig, default_config


class AgentState(BaseModel):
    """Agent 状态"""
    messages: List[Any] = Field(default_factory=list)
    user_context: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class OfficeAgent:
    """
    Office Agent 核心类
    
    基于 LangChain ReAct 架构的办公助手 Agent，
    支持工具调用、记忆管理和多轮对话
    """
    
    def __init__(
        self,
        config: Optional[OfficeAgentConfig] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None
    ):
        """
        初始化 Office Agent
        
        Args:
            config: Agent 配置
            tools: 工具列表
            system_prompt: 自定义系统提示
        """
        self.config = config or default_config
        self.tools = tools or []
        
        # 初始化 LLM
        self._init_llm()
        
        # 初始化记忆系统
        self._init_memory()
        
        # 初始化 Agent
        self._init_agent(system_prompt)
        
        # 状态管理
        self.state = AgentState()
    
    def _init_llm(self):
        """初始化 LLM"""
        llm_config = self.config.llm
        
        self.llm = ChatOpenAI(
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens
        )
    
    def _init_memory(self):
        """初始化记忆系统"""
        memory_config = self.config.memory
        
        if memory_config.type == "summary":
            self.memory = ConversationSummaryMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True
            )
        else:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
    
    def _init_agent(self, system_prompt: Optional[str] = None):
        """初始化 Agent"""
        # 系统提示词
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # 构建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建 ReAct Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 创建 Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.config.agent.verbose,
            handle_parsing_errors=self.config.agent.handle_parsing_errors,
            max_iterations=self.config.agent.max_iterations,
            early_stopping_method=self.config.agent.early_stopping_method
        )
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个专业、高效的办公助手，帮助用户处理日常工作。

你的核心能力包括：
1. 📧 邮件管理 - 发送、回复、搜索和整理邮件
2. 📅 日程安排 - 创建会议、检查时间、发送邀请
3. 📄 文档处理 - 读取、总结、创建和编辑文档
4. ✅ 任务管理 - 创建、更新和追踪任务

工作原则：
- 始终使用工具完成任务，不要仅靠猜测
- 确认重要操作前先询问用户
- 提供清晰、结构化的回复
- 主动识别可以自动化的重复性工作
- 尊重用户隐私，不泄露敏感信息

当不确定如何操作时，诚实地告诉用户，并提供可能的解决方案。"""
    
    def add_tool(self, tool: BaseTool) -> None:
        """
        动态添加工具
        
        Args:
            tool: LangChain 工具实例
        """
        self.tools.append(tool)
        self._rebuild_agent()
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """
        批量添加工具
        
        Args:
            tools: 工具列表
        """
        self.tools.extend(tools)
        self._rebuild_agent()
    
    def remove_tool(self, tool_name: str) -> bool:
        """
        移除工具
        
        Args:
            tool_name: 工具名称
        
        Returns:
            是否成功移除
        """
        original_len = len(self.tools)
        self.tools = [t for t in self.tools if t.name != tool_name]
        
        if len(self.tools) < original_len:
            self._rebuild_agent()
            return True
        return False
    
    def _rebuild_agent(self):
        """重建 Agent（添加工具后调用）"""
        self._init_agent(self.system_prompt)
    
    def process(self, user_input: str, **kwargs) -> str:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            **kwargs: 额外参数
        
        Returns:
            Agent 响应
        """
        result = self.agent_executor.invoke(
            {"input": user_input, **kwargs},
            config={"recursion_limit": 500}
        )
        return result["output"]
    
    async def aprocess(self, user_input: str, **kwargs) -> str:
        """
        异步处理用户输入
        
        Args:
            user_input: 用户输入
            **kwargs: 额外参数
        
        Returns:
            Agent 响应
        """
        result = await self.agent_executor.ainvoke(
            {"input": user_input, **kwargs},
            config={"recursion_limit": 500}
        )
        return result["output"]
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        """
        聊天接口，返回完整结果
        
        Args:
            user_input: 用户输入
        
        Returns:
            包含 output 和 intermediate_steps 的字典
        """
        result = self.agent_executor.invoke(
            {"input": user_input},
            config={"recursion_limit": 500}
        )
        return {
            "output": result["output"],
            "intermediate_steps": result.get("intermediate_steps", [])
        }
    
    def clear_memory(self) -> None:
        """清除记忆"""
        self.memory.clear()
    
    def get_memory_variables(self) -> Dict[str, Any]:
        """获取记忆变量"""
        return self.memory.load_memory_variables({})
    
    def set_user_context(self, context: Dict[str, Any]) -> None:
        """
        设置用户上下文
        
        Args:
            context: 上下文字典
        """
        self.state.user_context = context
    
    def get_session_id(self) -> Optional[str]:
        """获取会话 ID"""
        return self.state.session_id
    
    def set_session_id(self, session_id: str) -> None:
        """
        设置会话 ID
        
        Args:
            session_id: 会话标识
        """
        self.state.session_id = session_id


def create_office_agent(
    config: Optional[OfficeAgentConfig] = None,
    tools: Optional[List[BaseTool]] = None
) -> OfficeAgent:
    """
    工厂函数：创建 Office Agent
    
    Args:
        config: Agent 配置
        tools: 工具列表
    
    Returns:
        OfficeAgent 实例
    """
    return OfficeAgent(config=config, tools=tools)
