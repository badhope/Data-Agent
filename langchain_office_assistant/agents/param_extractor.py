"""
智能参数提取器
使用LLM进行语义理解，替代硬编码正则表达式
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import json
import logging

logger = logging.getLogger(__name__)


class ExtractedParams(BaseModel):
    """提取的参数模型"""
    tool_name: str = Field(description="要调用的工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    confidence: float = Field(ge=0.0, le=1.0, description="参数提取置信度")
    reasoning: str = Field(default="", description="提取推理过程")


class SmartParamExtractor:
    """智能参数提取器"""

    TOOL_SCHEMAS = {
        "send_email": {
            "params": ["to", "subject", "body"],
            "required": ["to", "subject"],
            "description": "发送邮件"
        },
        "search_emails": {
            "params": ["keyword", "limit"],
            "required": ["keyword"],
            "description": "搜索邮件"
        },
        "check_calendar": {
            "params": ["date"],
            "required": ["date"],
            "description": "查询日程"
        },
        "schedule_meeting": {
            "params": ["title", "date", "time", "duration_minutes", "participants"],
            "required": ["title", "date", "time"],
            "description": "创建会议"
        },
        "create_task": {
            "params": ["title", "description", "priority", "due_date"],
            "required": ["title"],
            "description": "创建任务"
        },
        "list_tasks": {
            "params": ["filter_status"],
            "required": [],
            "description": "列出任务"
        },
        "read_document": {
            "params": ["file_path"],
            "required": ["file_path"],
            "description": "读取文档"
        },
        "write_document": {
            "params": ["file_path", "content"],
            "required": ["file_path", "content"],
            "description": "写入文档"
        },
        "create_ppt": {
            "params": ["title", "template"],
            "required": ["title"],
            "description": "创建PPT"
        },
        "search_knowledge": {
            "params": ["query", "top_k"],
            "required": ["query"],
            "description": "搜索知识库"
        },
        "add_document": {
            "params": ["content", "title", "metadata"],
            "required": ["content", "title"],
            "description": "添加文档到知识库"
        },
        "create_line_chart": {
            "params": ["title", "x_data", "y_data"],
            "required": ["x_data", "y_data"],
            "description": "创建折线图"
        },
        "create_bar_chart": {
            "params": ["title", "labels", "values"],
            "required": ["labels", "values"],
            "description": "创建柱状图"
        },
        "create_pie_chart": {
            "params": ["title", "labels", "values"],
            "required": ["labels", "values"],
            "description": "创建饼图"
        },
        "calculate": {
            "params": ["expression"],
            "required": ["expression"],
            "description": "计算数学表达式"
        },
        "statistics": {
            "params": ["numbers"],
            "required": ["numbers"],
            "description": "统计分析"
        },
        "currency_convert": {
            "params": ["amount", "from_currency", "to_currency"],
            "required": ["amount", "from_currency", "to_currency"],
            "description": "货币转换"
        },
        "unit_convert": {
            "params": ["value", "from_unit", "to_unit"],
            "required": ["value", "from_unit", "to_unit"],
            "description": "单位转换"
        },
        "date_diff": {
            "params": ["date1", "date2", "unit"],
            "required": ["date1", "date2"],
            "description": "计算日期差"
        },
    }

    def __init__(self, model_name: str = "qwen-plus", api_key: str = None, api_base: str = None):
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=api_base,
            temperature=0.1
        )
        self.parser = PydanticOutputParser(pydantic_object=ExtractedParams)
        self._init_chain()

    def _init_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个参数提取专家。从用户输入中提取工具调用所需的参数。

工具信息：
{tool_info}

提取规则：
1. 仔细分析用户意图，选择最合适的工具
2. 从用户输入中提取所有相关参数
3. 如果缺少必需参数，使用合理的默认值
4. 给出0-1之间的置信度分数
5. 简要说明你的推理过程

{format_instructions}

注意：必须返回有效的JSON格式。"""),
            ("human", "{user_input}")
        ])

        self.chain = prompt | self.llm | self.parser

    def extract(self, user_input: str, intent: str, available_tools: List[str] = None) -> ExtractedParams:
        """智能提取参数"""
        available_tools = available_tools or list(self.TOOL_SCHEMAS.keys())

        tool_info = []
        for tool_name in available_tools:
            if tool_name in self.TOOL_SCHEMAS:
                schema = self.TOOL_SCHEMAS[tool_name]
                tool_info.append(f"- {tool_name}: {schema['description']}")
                tool_info.append(f"  参数: {', '.join(schema['params'])}")
                tool_info.append(f"  必需: {', '.join(schema['required'])}")

        try:
            result = self.chain.invoke({
                "user_input": user_input,
                "tool_info": "\n".join(tool_info),
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"LLM参数提取失败: {e}")
            return self._fallback_extract(user_input, intent)

    def _fallback_extract(self, user_input: str, intent: str) -> ExtractedParams:
        """降级方案：简单关键词提取"""
        import re
        from datetime import datetime

        params = {}
        tool_name = "unknown"

        intent_lower = intent.lower() if intent else ""
        input_lower = user_input.lower()

        if "email" in intent_lower or "邮件" in input_lower:
            if "发送" in input_lower or "发" in input_lower:
                tool_name = "send_email"
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
                params["to"] = emails if emails else ["assistant@company.com"]
                params["subject"] = "无主题"
                params["body"] = user_input
            else:
                tool_name = "search_emails"
                params["keyword"] = user_input

        elif "calendar" in intent_lower or "日程" in input_lower or "会议" in input_lower:
            if "创建" in input_lower or "安排" in input_lower:
                tool_name = "schedule_meeting"
                params["title"] = "新会议"
                params["date"] = datetime.now().strftime("%Y-%m-%d")
                params["time"] = "14:00"
            else:
                tool_name = "check_calendar"
                params["date"] = datetime.now().strftime("%Y-%m-%d")

        elif "task" in intent_lower or "任务" in input_lower:
            if "列表" in input_lower or "查看" in input_lower:
                tool_name = "list_tasks"
            else:
                tool_name = "create_task"
                params["title"] = user_input

        elif "chart" in intent_lower or "图表" in input_lower:
            if "折线" in input_lower:
                tool_name = "create_line_chart"
            elif "柱" in input_lower:
                tool_name = "create_bar_chart"
            elif "饼" in input_lower:
                tool_name = "create_pie_chart"
            else:
                tool_name = "create_bar_chart"

            numbers = re.findall(r'\d+\.?\d*', user_input)
            params["labels"] = [f"类别{i+1}" for i in range(len(numbers))]
            params["values"] = [float(n) for n in numbers] if numbers else [10, 20, 30, 40]
            params["title"] = "数据图表"

        elif "calc" in intent_lower or "计算" in input_lower:
            if "货币" in input_lower or "换算" in input_lower:
                tool_name = "currency_convert"
                numbers = re.findall(r'\d+\.?\d*', user_input)
                params["amount"] = float(numbers[0]) if numbers else 100
                params["from_currency"] = "USD"
                params["to_currency"] = "CNY"
            elif "统计" in input_lower:
                tool_name = "statistics"
                numbers = re.findall(r'\d+\.?\d*', user_input)
                params["numbers"] = [float(n) for n in numbers] if numbers else [1, 2, 3, 4, 5]
            else:
                tool_name = "calculate"
                calc_match = re.search(r'[\d\s\+\-\*\/\(\)\.]+', user_input)
                params["expression"] = calc_match.group().strip() if calc_match else "2+2"

        elif "knowledge" in intent_lower or "知识" in input_lower:
            if "添加" in input_lower:
                tool_name = "add_document"
                params["content"] = user_input
                params["title"] = "新文档"
            else:
                tool_name = "search_knowledge"
                params["query"] = user_input

        else:
            tool_name = "calculate"
            params["expression"] = "2+2"

        return ExtractedParams(
            tool_name=tool_name,
            params=params,
            confidence=0.5,
            reasoning="使用降级方案提取"
        )
