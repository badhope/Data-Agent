from typing import List, Dict, Any, Optional
from enum import Enum
from langchain_openai import ChatOpenAI
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
- knowledge：知识库相关操作（搜索、问答、文档上传、知识管理）
- chart：图表相关操作（生成折线图、柱状图、雷达图等）
- calc：计算相关操作（公式计算、统计分析、单位转换）
- chat：普通对话，不需要调用工具

重要：请输出完整的JSON格式，必须包含以下所有字段：
- intent：意图类型
- confidence：置信度（0到1之间的数字）
- entities：实体信息对象
- requires_tool：是否需要工具（true或false）

示例：{"intent": "email", "confidence": 0.95, "entities": {}, "requires_tool": true}"""

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
                data = json.loads(json_str)

                if "intent" in data:
                    intent = data["intent"]
                    confidence = data.get("confidence", 0.9)
                    entities = data.get("entities", {})
                    requires_tool = data.get("requires_tool", True)

                    return IntentResult(
                        intent=intent,
                        confidence=confidence,
                        entities=entities,
                        requires_tool=requires_tool
                    )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"JSON parse error: {e}")

        return self._fallback_recognize(content)

    def _fallback_recognize(self, user_input: str) -> IntentResult:
        input_lower = user_input.lower()

        knowledge_patterns = ["知识库", "知识管理", "添加到知识", "上传到知识"]
        if any(p in user_input for p in knowledge_patterns):
            return IntentResult(
                intent="knowledge",
                confidence=0.9,
                entities={"keyword": "知识库"},
                requires_tool=True
            )

        if "搜索" in user_input and "知识" in user_input:
            return IntentResult(
                intent="knowledge",
                confidence=0.9,
                entities={"keyword": "搜索知识"},
                requires_tool=True
            )

        if "搜索" in user_input and ("邮件" in user_input or "email" in input_lower):
            return IntentResult(
                intent="email",
                confidence=0.9,
                entities={"keyword": "邮件搜索"},
                requires_tool=True
            )

        if "创建" in user_input and "任务" in user_input:
            return IntentResult(
                intent="task",
                confidence=0.9,
                entities={"keyword": "创建任务"},
                requires_tool=True
            )

        if "任务" in user_input:
            return IntentResult(
                intent="task",
                confidence=0.85,
                entities={},
                requires_tool=True
            )

        if "日历" in user_input or "会议" in user_input or "日程" in user_input:
            return IntentResult(
                intent="calendar",
                confidence=0.9,
                entities={},
                requires_tool=True
            )

        if "ppt" in input_lower or "演示" in user_input or "幻灯片" in user_input:
            return IntentResult(
                intent="ppt",
                confidence=0.9,
                entities={},
                requires_tool=True
            )

        if any(p in user_input for p in ["柱状图", "折线图", "饼图", "雷达图", "散点图"]):
            return IntentResult(
                intent="chart",
                confidence=0.9,
                entities={},
                requires_tool=True
            )

        if "图表" in user_input:
            return IntentResult(
                intent="chart",
                confidence=0.85,
                entities={},
                requires_tool=True
            )

        if any(p in user_input for p in ["计算", "统计", "转换", "等于多少", "货币"]):
            return IntentResult(
                intent="calc",
                confidence=0.9,
                entities={},
                requires_tool=True
            )

        if "邮件" in user_input or "email" in input_lower:
            return IntentResult(
                intent="email",
                confidence=0.9,
                entities={},
                requires_tool=True
            )

        if "文档" in user_input or "文件" in user_input:
            return IntentResult(
                intent="document",
                confidence=0.8,
                entities={},
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
