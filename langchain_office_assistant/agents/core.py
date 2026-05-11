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
        from langchain_office_assistant.utils.config import config as global_config

        self.config = config or {}
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
        self.memory_manager = MemoryManager(self.redis_url)
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
        tool_name = self._select_tool(intent_type=intent_result.intent, user_input=user_input)
        params = self._extract_params(user_input, intent_result.intent, tool_name)

        self.trace_recorder.add_step(
            trace_id,
            "tool_selection",
            tool_name=tool_name,
            input_params={"user_input": user_input, "params": params}
        )

        try:
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

    def _select_tool(self, intent_type: str, user_input: str) -> str:
        intent_lower = intent_type.lower()
        input_lower = user_input.lower()

        tool_map = {
            "email": [
                ("发送", "send_email"),
                ("搜索", "search_emails"),
                ("查看", "read_email"),
            ],
            "calendar": [
                ("创建", "schedule_meeting"),
                ("查询", "check_calendar"),
                ("查看", "check_calendar"),
            ],
            "task": [
                ("创建", "create_task"),
                ("列表", "list_tasks"),
                ("更新", "update_task"),
                ("完成", "update_task"),
            ],
            "document": [
                ("读取", "read_document"),
                ("写入", "write_document"),
                ("搜索", "search_documents"),
            ],
            "ppt": [
                ("创建", "create_ppt"),
                ("添加", "add_slide"),
                ("图表", "add_chart_to_ppt"),
            ],
            "knowledge": [
                ("搜索", "search_knowledge"),
                ("查询", "search_knowledge"),
                ("添加", "add_document"),
                ("列表", "list_documents"),
            ],
            "chart": [
                ("折线", "create_line_chart"),
                ("柱状", "create_bar_chart"),
                ("饼", "create_pie_chart"),
                ("雷达", "create_radar_chart"),
                ("散点", "create_scatter_plot"),
            ],
            "calc": [
                ("货币", "currency_convert"),
                ("单位", "unit_convert"),
                ("日期", "date_diff"),
                ("统计", "statistics"),
                ("计算", "calculate"),
            ],
        }

        tools = tool_map.get(intent_lower, [])
        for keyword, tool_name in tools:
            if keyword in input_lower:
                return tool_name

        if tools:
            return tools[0][1]
        return "unknown"

    def _extract_params(self, user_input: str, intent_type: str, tool_name: str) -> Dict:
        params = {}
        input_lower = user_input.lower()

        import re

        if tool_name == "send_email":
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
            if not emails:
                emails = ["assistant@company.com"]
            params["to"] = emails
            subject_match = re.search(r'主题[：:](.+?)(?:\n|$)', user_input)
            params["subject"] = subject_match.group(1) if subject_match else "无主题"
            body_match = re.search(r'内容[：:](.+?)$', user_input, re.DOTALL)
            params["body"] = body_match.group(1) if body_match else user_input

        elif tool_name == "search_emails":
            keywords = re.findall(r'关于(.+?)的|的(.+?)邮件', user_input)
            if keywords:
                params["keyword"] = ' '.join([k for k in keywords[0] if k])
            else:
                params["keyword"] = re.sub(r'[^\w\s]', '', user_input)

        elif tool_name == "read_email":
            params["email_id"] = "email_001"

        elif tool_name == "check_calendar":
            date_match = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', user_input)
            params["date"] = date_match.group() if date_match else datetime.now().strftime("%Y-%m-%d")

        elif tool_name == "schedule_meeting":
            params["title"] = re.sub(r'.*创建.*?的?(.+?)(?:会议|日程)', r'\1', user_input) or "新会议"
            date_match = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', user_input)
            params["date"] = date_match.group() if date_match else datetime.now().strftime("%Y-%m-%d")
            time_match = re.search(r'(\d{1,2})[时点:](\d{0,2})', user_input)
            params["time"] = time_match.group().replace('点', ':00') if time_match else "14:00"
            params["duration_minutes"] = 60
            params["participants"] = []

        elif tool_name == "create_task":
            params["title"] = re.sub(r'.*创建.*?的?(.+?)(?:任务|todo)', r'\1', user_input) or "新任务"
            desc_match = re.search(r'描述[：:](.+?)(?:\n|$)', user_input)
            params["description"] = desc_match.group(1) if desc_match else ""

        elif tool_name == "list_tasks":
            if "进行中" in input_lower:
                params["filter_status"] = "in_progress"
            elif "已完成" in input_lower:
                params["filter_status"] = "completed"
            elif "待办" in input_lower:
                params["filter_status"] = "pending"

        elif tool_name == "update_task":
            params["task_id"] = "task_001"
            if "完成" in input_lower:
                params["status"] = "completed"

        elif tool_name in ["read_document", "write_document", "search_documents"]:
            params["file_path"] = "document.txt"

        elif tool_name == "create_ppt":
            params["title"] = re.sub(r'.*创建.*?的?(.+?)(?:PPT|演示)', r'\1', user_input) or "新演示文稿"

        elif tool_name in ["add_slide", "add_chart_to_ppt"]:
            params["instance_id"] = "ppt_temp"
            params["title"] = "新幻灯片"

        elif tool_name == "save_ppt":
            params["instance_id"] = "ppt_temp"
            params["file_path"] = "output.pptx"

        elif tool_name == "search_knowledge":
            params["query"] = user_input.replace("搜索", "").replace("知识库", "").strip()

        elif tool_name == "add_document":
            params["content"] = user_input
            params["title"] = "新文档"

        elif tool_name == "list_documents":
            pass

        elif tool_name in ["create_line_chart", "create_bar_chart", "create_pie_chart", "create_radar_chart", "create_scatter_plot"]:
            params["title"] = "图表"
            numbers = re.findall(r'\d+\.?\d*', user_input)
            if tool_name == "create_line_chart":
                params["x_data"] = [f"点{i+1}" for i in range(len(numbers))]
                params["y_data"] = [float(n) for n in numbers[:10]]
            else:
                params["labels"] = [f"类别{i+1}" for i in range(len(numbers))]
                params["values"] = [float(n) for n in numbers[:10]]

        elif tool_name == "calculate":
            calc_match = re.search(r'[\d\s\+\-\*\/\(\)\.]+', user_input.replace('计算', ''))
            params["expression"] = calc_match.group() if calc_match else "2+2"

        elif tool_name == "statistics":
            numbers = re.findall(r'\d+\.?\d*', user_input)
            params["numbers"] = [float(n) for n in numbers] if numbers else [1, 2, 3, 4, 5]

        elif tool_name == "currency_convert":
            amount_match = re.findall(r'(\d+\.?\d*)\s*([A-Za-z]{3})', user_input)
            if len(amount_match) >= 2:
                params["amount"] = float(amount_match[0][0])
                params["from_currency"] = amount_match[0][1].upper()
                params["to_currency"] = amount_match[1][1].upper()
            else:
                amount_match = re.findall(r'(\d+\.?\d*)', user_input)
                params["amount"] = float(amount_match[0]) if amount_match else 100
                params["from_currency"] = "USD" if "美元" in input_lower or "usd" in input_lower else "CNY"
                params["to_currency"] = "CNY" if "人民币" in input_lower or "cny" in input_lower else "USD"

        elif tool_name == "unit_convert":
            params["value"] = 1.0
            params["from_unit"] = "m"
            params["to_unit"] = "km"

        elif tool_name == "date_diff":
            dates = re.findall(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', user_input)
            params["date1"] = dates[0] if len(dates) > 0 else "2025-01-01"
            params["date2"] = dates[1] if len(dates) > 1 else datetime.now().strftime("%Y-%m-%d")

        return {k: v for k, v in params.items() if v or v == 0}

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
