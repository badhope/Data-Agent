from typing import List, Dict, Any, Optional
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_office_assistant.utils.logger import get_logger
from langchain_office_assistant.utils.config import config
import json
import re

logger = get_logger(__name__)

class IntentType(str, Enum):
    EMAIL = "email"
    CALENDAR = "calendar"
    TASK = "task"
    DOCUMENT = "document"
    PPT = "ppt"
    KNOWLEDGE = "knowledge"
    CHART = "chart"
    CALC = "calc"
    CHAT = "chat"
    UNKNOWN = "unknown"

class IntentResult(BaseModel):
    intent: str = Field(description="识别的意图类型")
    confidence: float = Field(description="置信度")
    entities: Dict[str, Any] = Field(description="提取的实体信息")
    requires_tool: bool = Field(description="是否需要调用工具")

class IntentRecognizer:
    def __init__(self, model_name: str = None, api_key: str = None, api_base: str = None):
        self.model_name = model_name or config.agent_model
        self.api_key = api_key or config.openai_api_key
        self.api_base = api_base or config.openai_api_base

        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.api_base,
            temperature=0
        )

    def recognize(self, user_input: str) -> IntentResult:
        try:
            system_msg = """你是一个意图识别专家，需要分析用户的输入并识别其意图。

可用的意图类型：
- email：邮件相关操作（发送、搜索、阅读邮件）
- calendar：日历相关操作（查询日程、创建会议、提醒）
- task：任务相关操作（创建、更新、列表、完成任务）
- document：文档相关操作（读取、写入、转换Word/Excel/PDF）
- ppt：PPT相关操作（创建演示文稿、添加幻灯片、图表嵌入）
- knowledge：知识库相关操作（搜索、问答、文档上传）
- chart：图表相关操作（生成折线图、柱状图、雷达图等）
- calc：计算相关操作（公式计算、统计分析、单位转换）
- chat：普通对话，不需要调用工具
- unknown：无法识别的意图

请直接输出JSON格式，不需要其他说明"""

            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=f"用户输入：{user_input}")
            ]

            response = self.llm.invoke(messages)
            content = response.content.strip()

            result = self._parse_json_response(content)
            logger.debug(f"Intent recognition result: {result}")
            return result
        except Exception as e:
            logger.error(f"Intent recognition failed: {e}")
            return self._fallback_recognize(user_input)

    def _parse_json_response(self, content: str) -> IntentResult:
        try:
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return IntentResult(**result)
        except json.JSONDecodeError:
            pass

        if "email" in content.lower():
            return IntentResult(intent="email", confidence=0.9, entities={}, requires_tool=True)
        elif "日历" in content or "calendar" in content.lower() or "会议" in content:
            return IntentResult(intent="calendar", confidence=0.9, entities={}, requires_tool=True)
        elif "任务" in content or "task" in content.lower():
            return IntentResult(intent="task", confidence=0.9, entities={}, requires_tool=True)
        elif "文档" in content or "document" in content.lower():
            return IntentResult(intent="document", confidence=0.9, entities={}, requires_tool=True)
        elif "ppt" in content.lower() or "演示" in content:
            return IntentResult(intent="ppt", confidence=0.9, entities={}, requires_tool=True)
        elif "知识" in content or "knowledge" in content.lower() or "搜索" in content:
            return IntentResult(intent="knowledge", confidence=0.9, entities={}, requires_tool=True)
        elif "图表" in content or "chart" in content.lower() or "图" in content:
            return IntentResult(intent="chart", confidence=0.9, entities={}, requires_tool=True)
        elif "计算" in content or "calc" in content.lower() or "统计" in content or "转换" in content:
            return IntentResult(intent="calc", confidence=0.9, entities={}, requires_tool=True)
        else:
            return IntentResult(intent="chat", confidence=0.9, entities={}, requires_tool=False)

    def _fallback_recognize(self, user_input: str) -> IntentResult:
        input_lower = user_input.lower()

        keywords = {
            "email": ["邮件", "email", "发送邮件", "搜索邮件"],
            "calendar": ["日历", "会议", "calendar", "日程"],
            "task": ["任务", "task", "todo"],
            "document": ["文档", "文件", "document", "pdf", "word"],
            "ppt": ["ppt", "演示", "幻灯片", "powerpoint"],
            "knowledge": ["知识", "知识库", "search", "搜索"],
            "chart": ["图表", "图", "chart", "柱状图", "折线图"],
            "calc": ["计算", "统计", "转换", "公式", "等于", "多少"],
        }

        for intent, words in keywords.items():
            for word in words:
                if word in input_lower or word in user_input:
                    return IntentResult(
                        intent=intent,
                        confidence=0.7,
                        entities={"keyword": word},
                        requires_tool=True
                    )

        return IntentResult(intent="chat", confidence=0.5, entities={}, requires_tool=False)

    def classify_intent(self, user_input: str) -> IntentType:
        result = self.recognize(user_input)
        return IntentType(result.intent)

    def get_intent_description(self, intent_type: IntentType) -> str:
        descriptions = {
            IntentType.EMAIL: "邮件管理",
            IntentType.CALENDAR: "日历管理",
            IntentType.TASK: "任务管理",
            IntentType.DOCUMENT: "文档处理",
            IntentType.PPT: "PPT生成",
            IntentType.KNOWLEDGE: "知识库检索",
            IntentType.CHART: "图表生成",
            IntentType.CALC: "计算工具",
            IntentType.CHAT: "普通对话",
            IntentType.UNKNOWN: "未知意图"
        }
        return descriptions.get(intent_type, "未知")
