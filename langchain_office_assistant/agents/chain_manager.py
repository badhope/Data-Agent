"""
对话链管理器
管理LangChain对话链的初始化和执行
"""
from typing import Dict, Any, Optional, Callable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ChainManager:
    """对话链管理器"""

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_func: Callable,
        system_prompt: str = None
    ):
        self.llm = llm
        self.memory_func = memory_func
        self.system_prompt = system_prompt or self._default_system_prompt()
        self._chain = None
        self._chain_with_history = None

    def _default_system_prompt(self) -> str:
        return """你是一个专业的办公智能体，具备多种办公能力：

可用工具：
- 📧 邮件插件：发送、搜索、阅读邮件
- 📅 日历插件：查询日程、创建会议、设置提醒
- ✅ 任务插件：创建、更新、列表、完成任务
- 📄 文档插件：读取、写入、转换Word/Excel/PDF文档
- 📊 PPT插件：创建演示文稿、添加幻灯片、嵌入图表
- 📚 知识库插件：向量检索、文档问答
- 📈 图表插件：生成折线图、柱状图、雷达图、散点图等
- 🧮 计算插件：公式计算、统计分析、单位转换

回复规则：
- 使用友好、专业的语言
- 对于复杂查询，提供详细的步骤说明
"""

    def initialize(self):
        """初始化对话链"""
        if self._chain is not None:
            return

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        self._chain = prompt | self.llm | StrOutputParser()
        self._chain_with_history = RunnableWithMessageHistory(
            self._chain,
            self.memory_func,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        logger.info("Chain initialized")

    @property
    def chain(self):
        """获取对话链"""
        if self._chain is None:
            self.initialize()
        return self._chain

    @property
    def chain_with_history(self):
        """获取带历史的对话链"""
        if self._chain_with_history is None:
            self.initialize()
        return self._chain_with_history

    def invoke(self, user_input: str, session_id: str = "default") -> str:
        """执行对话"""
        return self.chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )

    def reset(self):
        """重置对话链"""
        self._chain = None
        self._chain_with_history = None
        logger.info("Chain reset")
