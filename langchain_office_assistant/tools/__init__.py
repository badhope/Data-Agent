"""Tools module - Office assistant tools."""

from typing import List, Optional
from langchain_core.tools import tool

# Import from submodules
from .email import send_email, search_emails, read_email
from .calendar import check_calendar, schedule_meeting
from .document import read_document, write_document


# ==================== Task Tools ====================

@tool
def create_task(title: str, description: Optional[str] = None, priority: str = "medium") -> str:
    """Create a new task."""
    return f"✅ Task created!\n\n📋 Title: {title}\n📝 Description: {description or 'None'}\n⭐ Priority: {priority}"


@tool
def list_tasks(filter_status: Optional[str] = None) -> str:
    """List all tasks, optionally filtered by status."""
    tasks = [
        {"id": "task_001", "title": "完成项目报告", "status": "in_progress", "priority": "high"},
        {"id": "task_002", "title": "代码审查", "status": "pending", "priority": "medium"},
        {"id": "task_003", "title": "团队周会", "status": "completed", "priority": "low"},
    ]
    
    if filter_status:
        tasks = [t for t in tasks if t["status"] == filter_status]
    
    if not tasks:
        return "No tasks found"
    
    output = f"📋 Task List ({len(tasks)} items):\n\n"
    for task in tasks:
        status_icon = {
            "pending": "○",
            "in_progress": "🔄",
            "completed": "✓"
        }.get(task["status"], "?")
        
        priority_icon = {
            "high": "⭐",
            "medium": "○",
            "low": "·"
        }.get(task["priority"], "·")
        
        output += f"{status_icon} {priority_icon} {task['title']}\n"
    
    return output


# Export all tools
__all__ = [
    "send_email",
    "search_emails",
    "read_email",
    "check_calendar",
    "schedule_meeting",
    "read_document",
    "write_document",
    "create_task",
    "list_tasks",
]
