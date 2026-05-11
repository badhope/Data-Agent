from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_office_assistant.agents.intent_recognizer import IntentRecognizer, IntentType
from langchain_office_assistant.agents.memory_manager import MemoryManager
from langchain_office_assistant.agents.trace_recorder import TraceRecorder
from langchain_office_assistant.plugins import (
    EmailPlugin,
    CalendarPlugin,
    TaskPlugin,
    DocumentPlugin,
    PPTPlugin,
    KnowledgePlugin,
    ChartPlugin,
    CalcPlugin,
)
from langchain_office_assistant.utils.logger import get_logger
from langchain_office_assistant.utils.config import config

logger = get_logger(__name__)

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
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model_name = self.config.get("agent_model", config.agent_model)
        self.api_key = self.config.get("openai_api_key", config.openai_api_key)
        self.api_base = self.config.get("openai_api_base", config.openai_api_base)

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
        self.memory_manager = MemoryManager(self.config.get("redis_url", config.redis_url))
        self.trace_recorder = TraceRecorder()

        self._init_plugins()
        self._init_chain()

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

            response, tool_used = await self._execute_intent(intent_type, user_input, intent_result, trace_id)

            total_duration = (datetime.now() - start_time).total_seconds() * 1000

            self.trace_recorder.finalize_trace(trace_id, response, int(total_duration))

            self.memory_manager.get_chat_history(session_id).add_message(
                self._create_human_message(user_input)
            )
            self.memory_manager.get_chat_history(session_id).add_message(
                self._create_ai_message(response)
            )

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
            return {
                "response": f"❌ 执行失败：{str(e)}",
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
        tool_name = self._infer_tool_name(intent_result)

        self.trace_recorder.add_step(
            trace_id,
            "tool_selection",
            tool_name=tool_name,
            input_params={"user_input": user_input, "entities": intent_result.entities}
        )

        try:
            params = self._extract_params(user_input, intent_result.entities, tool_name)

            start_time = datetime.now()
            result = await plugin.execute(tool_name, **params)
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            self.trace_recorder.add_step(
                trace_id,
                "tool_execution",
                tool_name=tool_name,
                input_params=params,
                output=str(result),
                duration_ms=int(duration_ms)
            )

            response = self._format_response(result, intent_result.intent)
            return response, tool_name

        except Exception as e:
            self.trace_recorder.add_step(
                trace_id,
                "tool_execution",
                tool_name=tool_name,
                error=str(e)
            )
            return f"❌ 工具执行失败：{str(e)}", tool_name

    def _infer_tool_name(self, intent_result: Any) -> str:
        entity_action = intent_result.entities.get("action", "")

        intent_tools = {
            IntentType.EMAIL: {
                "send": "send_email",
                "search": "search_emails",
                "read": "read_email",
            },
            IntentType.CALENDAR: {
                "create": "check_calendar",
                "list": "check_calendar",
                "search": "check_calendar",
            },
            IntentType.TASK: {
                "create": "create_task",
                "list": "list_tasks",
                "update": "update_task",
                "complete": "update_task",
            },
            IntentType.DOCUMENT: {
                "read": "read_document",
                "write": "write_document",
                "search": "search_documents",
            },
            IntentType.PPT: {
                "create": "create_ppt",
                "add": "add_slide",
                "chart": "add_chart_to_ppt",
            },
            IntentType.KNOWLEDGE: {
                "search": "search_knowledge",
                "query": "search_knowledge",
                "add": "add_document",
                "list": "list_documents",
            },
            IntentType.CHART: {
                "line": "create_line_chart",
                "bar": "create_bar_chart",
                "pie": "create_pie_chart",
                "radar": "create_radar_chart",
                "scatter": "create_scatter_plot",
            },
            IntentType.CALC: {
                "calculate": "calculate",
                "statistics": "statistics",
                "convert": "currency_convert",
                "date": "date_diff",
                "unit": "unit_convert",
            },
        }

        intent_type = IntentType(intent_result.intent)
        tools = intent_tools.get(intent_type, {})

        for action, tool_name in tools.items():
            if action.lower() in entity_action.lower() or action.lower() in intent_result.intent:
                return tool_name

        return list(tools.values())[0] if tools else "unknown"

    def _extract_params(self, user_input: str, entities: Dict, tool_name: str) -> Dict:
        params = {}

        if tool_name == "send_email":
            params["to"] = entities.get("recipient", [""])
            params["subject"] = entities.get("subject", "")
            params["body"] = entities.get("body", "")

        elif tool_name == "search_emails":
            params["keyword"] = entities.get("keyword", user_input)

        elif tool_name == "read_email":
            params["email_id"] = entities.get("email_id", "")

        elif tool_name == "check_calendar":
            params["date"] = entities.get("date", "")

        elif tool_name == "create_task":
            params["title"] = entities.get("title", "")
            params["description"] = entities.get("description", "")
            params["due_date"] = entities.get("due_date", "")

        elif tool_name == "list_tasks":
            params["filter_status"] = entities.get("status")

        elif tool_name == "update_task":
            params["task_id"] = entities.get("task_id", "")
            params["status"] = entities.get("status")
            params["priority"] = entities.get("priority")

        elif tool_name == "read_document":
            params["file_path"] = entities.get("file_path", "")

        elif tool_name == "write_document":
            params["file_path"] = entities.get("file_path", "")
            params["content"] = entities.get("content", "")

        elif tool_name == "create_ppt":
            params["title"] = entities.get("title", "")

        elif tool_name == "add_slide":
            params["instance_id"] = entities.get("instance_id", "")
            params["title"] = entities.get("title", "")
            params["content"] = entities.get("content", "")

        elif tool_name == "add_chart_to_ppt":
            params["instance_id"] = entities.get("instance_id", "")
            params["chart_type"] = entities.get("chart_type", "bar")
            params["title"] = entities.get("title", "")

        elif tool_name == "search_knowledge":
            params["query"] = entities.get("query", user_input)

        elif tool_name == "add_document":
            params["content"] = entities.get("content", "")
            params["title"] = entities.get("title", "")

        elif tool_name == "list_documents":
            pass

        elif tool_name == "create_line_chart":
            params["title"] = entities.get("title", "")
            params["x_data"] = entities.get("x_data", [])
            params["y_data"] = entities.get("y_data", [])

        elif tool_name == "create_bar_chart":
            params["title"] = entities.get("title", "")
            params["labels"] = entities.get("labels", [])
            params["values"] = entities.get("values", [])

        elif tool_name == "create_pie_chart":
            params["title"] = entities.get("title", "")
            params["labels"] = entities.get("labels", [])
            params["values"] = entities.get("values", [])

        elif tool_name == "calculate":
            params["expression"] = entities.get("expression", "")

        elif tool_name == "statistics":
            params["numbers"] = entities.get("numbers", [])

        elif tool_name == "currency_convert":
            params["amount"] = entities.get("amount", 0)
            params["from_currency"] = entities.get("from_currency", "")
            params["to_currency"] = entities.get("to_currency", "")

        return {k: v for k, v in params.items() if v}

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
            output=str(result)
        )

        return result

    def _create_human_message(self, content: str):
        from langchain_core.messages import HumanMessage
        return HumanMessage(content=content)

    def _create_ai_message(self, content: str):
        from langchain_core.messages import AIMessage
        return AIMessage(content=content)

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

def create_office_agent(config: Dict = None) -> OfficeAgent:
    return OfficeAgent(config)

async def run_office_assistant(user_input: str, session_id: str = None, config: Dict = None) -> Dict[str, Any]:
    agent = create_office_agent(config)
    return await agent.run(user_input, session_id)
