from typing import List, Dict, Any, Optional
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_office_assistant.utils.logger import get_logger
from langchain_office_assistant.utils.config import config

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
    confidence: float = Field(description="置信度 (0-1)")
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
        self.parser = JsonOutputParser(pydantic_object=IntentResult)
        self.prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个意图识别专家，需要分析用户的输入并识别其意图。

可用的意图类型：
- email: 邮件相关操作（发送、搜索、阅读邮件）
- calendar: 日历相关操作（查询日程、创建会议、提醒）
- task: 任务相关操作（创建、更新、列表、完成任务）
- document: 文档相关操作（读取、写入、转换Word/Excel/PDF）
- ppt: PPT相关操作（创建演示文稿、添加幻灯片、图表嵌入）
- knowledge: 知识库相关操作（搜索、问答、文档上传）
- chart: 图表相关操作（生成折线图、柱状图、雷达图等）
- calc: 计算相关操作（公式计算、统计分析、单位转换）
- chat: 普通对话，不需要调用工具
- unknown: 无法识别的意图

请输出JSON格式，包含以下字段：
- intent: 识别的意图类型
- confidence: 置信度 (0-1)
- entities: 从输入中提取的关键实体信息
- requires_tool: 是否需要调用工具

示例：
输入: "帮我发送一封邮件给张三"
输出: {"intent": "email", "confidence": 0.95, "entities": {"action": "send", "recipient": "张三"}, "requires_tool": true}

输入: "你好，今天天气怎么样？"
输出: {"intent": "chat", "confidence": 0.9, "entities": {}, "requires_tool": false}"""),
            ("human", "用户输入: {input}"),
            ("human", "请按照JSON格式输出意图识别结果：")
        ])
        return prompt

    def recognize(self, user_input: str) -> IntentResult:
        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({"input": user_input})
            logger.debug(f"Intent recognition result: {result}")
            return result
        except Exception as e:
            logger.error(f"Intent recognition failed: {e}")
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                requires_tool=False
            )

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
