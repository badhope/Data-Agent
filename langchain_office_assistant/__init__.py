"""LangChain Office Assistant - Built on LangChain Framework."""

from langchain_office_assistant.tools import (
    ALL_OFFICE_TOOLS,
    EMAIL_TOOLS,
    CALENDAR_TOOLS,
    TASK_TOOLS,
    DOCUMENT_TOOLS,
    send_email,
    search_emails,
    read_email,
    check_calendar,
    schedule_meeting,
    create_task,
    list_tasks,
    search_documents,
    summarize_document,
)

from langchain_office_assistant.agents import (
    create_office_agent,
    run_office_assistant,
    SYSTEM_PROMPT,
)


__all__ = [
    "ALL_OFFICE_TOOLS",
    "EMAIL_TOOLS",
    "CALENDAR_TOOLS",
    "TASK_TOOLS",
    "DOCUMENT_TOOLS",
    "send_email",
    "search_emails",
    "read_email",
    "check_calendar",
    "schedule_meeting",
    "create_task",
    "list_tasks",
    "search_documents",
    "summarize_document",
    "create_office_agent",
    "run_office_assistant",
    "SYSTEM_PROMPT",
]
