"""
Office Agent 核心模块 - 重构版
集成智能参数提取、置信度处理、输出验证、错误恢复
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from .intent_recognizer import IntentRecognizer, IntentType
from .memory_manager import MemoryManager
from .trace_recorder import TraceRecorder
from .param_extractor import SmartParamExtractor, ExtractedParams
from .validators import (
    ConfidenceHandler,
    LLMOutputValidator,
    ErrorRecovery,
    ValidationResult
)
from ..plugins import (
    EmailPlugin,
    CalendarPlugin,
    TaskPlugin,
    DocumentPlugin,
    PPTPlugin,
    KnowledgePlugin,
    ChartPlugin,
    CalcPlugin,
)
from ..utils.logger import get_logger
from ..utils.config import config
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的办公智能体，具备多种办公能力：

可用工具：
- 📧 邮件插件：发送、搜索、阅读邮件
- 📅 日历插件：查询日程、创建会议、设置提醒
- ✅ 任务插件：创建、更新、列表、完成任务
- 📄 文档插件：读取、写入、转换Word/Excel/PDF文档
- 📊 PPT插件：创建演示文稿、添加幻灯片、嵌入图表
- 📚 知识库插件：向量检索、文档问答
- 📈 图表插件：生成折线图、柱状图、雷达图、散点图等
- 🧮 计算插件：公式计算、统计分析、单位转换

工作流程：
1. 识别用户意图
2. 选择合适的工具执行
3. 根据工具结果生成自然语言回复

当调用工具时，需要详细记录执行步骤以便追溯。

回复规则：
- 使用友好、专业的语言
- 对于复杂查询，提供详细的步骤说明
- 如果需要调用工具，记录完整的执行过程
"""


class OfficeAgent:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_dict: Dict = None):
        if self._initialized:
            return

        from langchain_office_assistant.utils.config import config as global_config

        self.config = config_dict or {}
        self.model_name = self.config.get("agent_model") or global_config.agent_model
        self.api_key = self.config.get("openai_api_key") or global_config.openai_api_key
        self.api_base = self.config.get("openai_api_base") or global_config.openai_api_base
        self.redis_url = self.config.get("redis_url") or global_config.redis_url

        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.api_base,
            temperature=0.7
        )

        self.intent_recognizer = IntentRecognizer(
            model_name=self.model_name,
            api_key=self.api_key,
            api_base=self.api_base
        )

        self.param_extractor = SmartParamExtractor(
            model_name=self.model_name,
            api_key=self.api_key,
            api_base=self.api_base
        )

        self.memory_manager = MemoryManager(self.redis_url)
        self.trace_recorder = TraceRecorder()

        self._init_plugins()
        self._init_chain()

        self._initialized = True
        logger.info("OfficeAgent initialized (singleton)")

    def _init_plugins(self):
        self.plugins = {
            IntentType.EMAIL: EmailPlugin(),
            IntentType.CALENDAR: CalendarPlugin(),
            IntentType.TASK: TaskPlugin(),
            IntentType.DOCUMENT: DocumentPlugin(),
            IntentType.PPT: PPTPlugin(),
            IntentType.KNOWLEDGE: KnowledgePlugin(),
            IntentType.CHART: ChartPlugin(),
            IntentType.CALC: CalcPlugin(),
        }

        for intent, plugin in self.plugins.items():
            plugin.initialize(self.config)
            logger.info(f"Plugin initialized: {intent.value}")

    def _init_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        self.chain = prompt | self.llm | StrOutputParser()
        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            lambda session_id: self.memory_manager.get_chat_history(session_id),
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    async def run(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        start_time = datetime.now()

        if not session_id:
            session_id = self.memory_manager.generate_session_id()

        intent_result = self.intent_recognizer.recognize(user_input)
        intent_type = IntentType(intent_result.intent)

        trace_id = self.trace_recorder.create_trace(session_id, user_input, intent_type.value)

        try:
            self.trace_recorder.add_step(
                trace_id,
                "intent_recognition",
                input_params={"user_input": user_input},
                output=intent_type.value,
                confidence=intent_result.confidence
            )

            if ConfidenceHandler.should_retry(intent_result.confidence):
                warning_msg = ConfidenceHandler.format_confidence_message(
                    intent_result.confidence, intent_type.value
                )
                self.trace_recorder.add_step(
                    trace_id,
                    "low_confidence_warning",
                    output=warning_msg
                )

            response, tool_used = await self._execute_intent(
                intent_type, user_input, intent_result, trace_id
            )

            total_duration = (datetime.now() - start_time).total_seconds() * 1000

            self.trace_recorder.finalize_trace(trace_id, response, int(total_duration))

            return {
                "response": response,
                "session_id": session_id,
                "trace_id": trace_id,
                "intent": intent_type.value,
                "confidence": intent_result.confidence,
                "tool_used": tool_used,
                "duration_ms": int(total_duration),
            }

        except Exception as e:
            self.trace_recorder.add_step(trace_id, "error", error=str(e))
            logger.error(f"Agent execution failed: {e}")

            recovery_suggestion = ErrorRecovery.generate_recovery_suggestion(str(e), "agent")
            return {
                "response": f"{recovery_suggestion}\n\n💡 您可以尝试重新描述您的需求。",
                "session_id": session_id,
                "trace_id": trace_id,
                "intent": intent_type.value,
                "confidence": intent_result.confidence,
                "tool_used": None,
                "duration_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            }

    async def _execute_intent(self, intent_type: IntentType, user_input: str,
                             intent_result: Any, trace_id: str) -> tuple:
        if intent_type in [IntentType.CHAT, IntentType.UNKNOWN]:
            response = await self._handle_direct_chat(user_input, trace_id)
            return response, None

        if intent_type not in self.plugins:
            response = await self._handle_direct_chat(user_input, trace_id)
            return response, None

        plugin = self.plugins[intent_type]
        return await self._execute_plugin(plugin, user_input, intent_result, trace_id)

    async def _execute_plugin(self, plugin, user_input: str, intent_result: Any, trace_id: str) -> tuple:
        extracted = self.param_extractor.extract(
            user_input,
            intent_result.intent,
            [tool.name for tool in plugin.get_tools()]
        )

        tool_name = extracted.tool_name
        params = extracted.params

        self.trace_recorder.add_step(
            trace_id,
            "param_extraction",
            tool_name=tool_name,
            input_params={"user_input": user_input, "extracted_params": params},
            confidence=extracted.confidence,
            reasoning=extracted.reasoning
        )

        validation_result = LLMOutputValidator.validate(tool_name, params, extracted.confidence)

        if validation_result.warnings:
            self.trace_recorder.add_step(
                trace_id,
                "validation_warnings",
                warnings=validation_result.warnings
            )

        if not validation_result.is_valid:
            error_msg = "参数验证失败: " + "; ".join(validation_result.errors)
            self.trace_recorder.add_step(
                trace_id,
                "validation_errors",
                errors=validation_result.errors
            )
            return f"❌ {error_msg}\n\n请检查您的输入并重试。", tool_name

        params = validation_result.corrected_params

        try:
            start_time = datetime.now()
            result = await plugin.execute(tool_name, **params)
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            self.trace_recorder.add_step(
                trace_id,
                "tool_execution",
                tool_name=tool_name,
                input_params=params,
                output=str(result)[:500],
                duration_ms=int(duration_ms)
            )

            confidence_msg = ConfidenceHandler.format_confidence_message(
                extracted.confidence, tool_name
            )
            response = self._format_response(result, intent_result.intent)
            if confidence_msg:
                response = f"{confidence_msg}\n\n{response}"

            return response, tool_name

        except Exception as e:
            self.trace_recorder.add_step(
                trace_id,
                "tool_execution",
                tool_name=tool_name,
                error=str(e)
            )
            recovery_msg = ErrorRecovery.generate_recovery_suggestion(str(e), tool_name)
            return f"{recovery_msg}", tool_name

    def _format_response(self, result: Any, intent: str) -> str:
        return str(result)

    async def _handle_direct_chat(self, user_input: str, trace_id: str) -> str:
        self.trace_recorder.add_step(
            trace_id,
            "direct_chat",
            input_params={"user_input": user_input}
        )

        result = self.chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": "direct_chat"}}
        )

        self.trace_recorder.add_step(
            trace_id,
            "direct_chat_response",
            output=str(result)[:500]
        )

        return result

    def get_trace_report(self, trace_id: str) -> str:
        return self.trace_recorder.visualize_trace(trace_id)

    def get_available_tools(self) -> List[Dict]:
        tools = []
        for intent, plugin in self.plugins.items():
            for tool in plugin.get_tools():
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "plugin": intent.value,
                })
        return tools


_agent_instance = None


def get_agent(config_dict: Dict = None) -> OfficeAgent:
    """获取全局Agent实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = OfficeAgent(config_dict)
    return _agent_instance


def create_office_agent(config: Dict = None) -> OfficeAgent:
    return get_agent(config)


async def run_office_assistant(user_input: str, session_id: str = None, config: Dict = None) -> Dict[str, Any]:
    agent = get_agent(config)
    return await agent.run(user_input, session_id)
