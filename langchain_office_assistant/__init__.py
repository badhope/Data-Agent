__version__ = "1.0.0"
__author__ = "Office Agent Team"

from langchain_office_assistant.agents import (
    OfficeAgent,
    create_office_agent,
    run_office_assistant,
    IntentRecognizer,
    MemoryManager,
    TraceRecorder,
    SYSTEM_PROMPT,
)

from langchain_office_assistant.plugins import (
    BasePlugin,
    EmailPlugin,
    CalendarPlugin,
    TaskPlugin,
    DocumentPlugin,
    PPTPlugin,
    KnowledgePlugin,
    ChartPlugin,
    CalcPlugin,
)

from langchain_office_assistant.utils import (
    Config,
    get_logger,
    format_datetime,
    validate_email,
    generate_session_id,
)

__all__ = [
    "__version__",
    "__author__",
    "OfficeAgent",
    "create_office_agent",
    "run_office_assistant",
    "IntentRecognizer",
    "MemoryManager",
    "TraceRecorder",
    "SYSTEM_PROMPT",
    "BasePlugin",
    "EmailPlugin",
    "CalendarPlugin",
    "TaskPlugin",
    "DocumentPlugin",
    "PPTPlugin",
    "KnowledgePlugin",
    "ChartPlugin",
    "CalcPlugin",
    "Config",
    "get_logger",
    "format_datetime",
    "validate_email",
    "generate_session_id",
]