"""
Office Agent Tools - All Tools Module
工具集统一导出
"""

from .email_tools import (
    send_email,
    search_emails,
    read_email,
    reply_email,
    list_email_folders,
    EMAIL_TOOLS
)

from .calendar_tools import (
    check_calendar,
    schedule_meeting,
    cancel_meeting,
    find_available_time,
    list_upcoming_meetings,
    CALENDAR_TOOLS
)

from .document_tools import (
    read_document,
    search_documents,
    summarize_document,
    create_document,
    list_documents,
    extract_action_items,
    DOCUMENT_TOOLS
)

from .task_tools import (
    create_task,
    update_task,
    complete_task,
    list_tasks,
    get_task_detail,
    delete_task,
    get_my_tasks,
    get_overdue_tasks,
    TASK_TOOLS,
    TaskStatus,
    TaskPriority
)


# 所有工具集合
ALL_TOOLS = (
    EMAIL_TOOLS +
    CALENDAR_TOOLS +
    DOCUMENT_TOOLS +
    TASK_TOOLS
)


# 按类别分组的工具
TOOLS_BY_CATEGORY = {
    "email": EMAIL_TOOLS,
    "calendar": CALENDAR_TOOLS,
    "document": DOCUMENT_TOOLS,
    "task": TASK_TOOLS
}


__all__ = [
    # Email Tools
    "send_email",
    "search_emails",
    "read_email",
    "reply_email",
    "list_email_folders",
    "EMAIL_TOOLS",
    
    # Calendar Tools
    "check_calendar",
    "schedule_meeting",
    "cancel_meeting",
    "find_available_time",
    "list_upcoming_meetings",
    "CALENDAR_TOOLS",
    
    # Document Tools
    "read_document",
    "search_documents",
    "summarize_document",
    "create_document",
    "list_documents",
    "extract_action_items",
    "DOCUMENT_TOOLS",
    
    # Task Tools
    "create_task",
    "update_task",
    "complete_task",
    "list_tasks",
    "get_task_detail",
    "delete_task",
    "get_my_tasks",
    "get_overdue_tasks",
    "TASK_TOOLS",
    "TaskStatus",
    "TaskPriority",
    
    # All Tools
    "ALL_TOOLS",
    "TOOLS_BY_CATEGORY"
]
