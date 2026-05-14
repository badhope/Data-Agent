from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.plugins.email import EmailPlugin
from langchain_office_assistant.plugins.calendar import CalendarPlugin
from langchain_office_assistant.plugins.task import TaskPlugin
from langchain_office_assistant.plugins.document import DocumentPlugin
from langchain_office_assistant.plugins.ppt import PPTPlugin
from langchain_office_assistant.plugins.knowledge import KnowledgePlugin
from langchain_office_assistant.plugins.chart import ChartPlugin
from langchain_office_assistant.plugins.calc import CalcPlugin

__all__ = [
    "BasePlugin",
    "EmailPlugin",
    "CalendarPlugin",
    "TaskPlugin",
    "DocumentPlugin",
    "PPTPlugin",
    "KnowledgePlugin",
    "ChartPlugin",
    "CalcPlugin",
]