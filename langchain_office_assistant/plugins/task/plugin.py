from typing import List, Dict, Any, Optional, Literal
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

class MockTaskStore:
    def __init__(self):
        self.tasks = [
            {
                "id": "task_001",
                "title": "完成项目报告",
                "description": "编写Q1季度项目进度报告",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2025-01-20",
            },
            {
                "id": "task_002",
                "title": "代码评审",
                "description": "评审新功能代码",
                "status": "pending",
                "priority": "medium",
                "due_date": "2025-01-18",
            }
        ]
        self.next_id = 3

    def create_task(self, data: dict) -> dict:
        task = {
            "id": f"task_{self.next_id:03d}",
            "status": "pending",
            **data
        }
        self.tasks.append(task)
        self.next_id += 1
        return task

    def get_all(self, filter_status: Optional[str] = None) -> List[dict]:
        if filter_status:
            return [t for t in self.tasks if t["status"] == filter_status]
        return self.tasks

    def update_task(self, task_id: str, data: dict) -> Optional[dict]:
        for task in self.tasks:
            if task["id"] == task_id:
                task.update(data)
                return task
        return None

class TaskPlugin(BasePlugin):
    name = "task"
    description = "任务管理插件 - 创建、列表、状态更新"

    def __init__(self):
        super().__init__()
        self.task_store = MockTaskStore()

    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"TaskPlugin initialized")

    def get_tools(self) -> List:
        return [create_task, list_tasks, update_task]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "create_task": create_task,
            "list_tasks": list_tasks,
            "update_task": update_task,
        }

        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"

        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def create_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[str] = None,
) -> str:
    """Create a new task."""
    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority not in valid_priorities:
        return f"❌ Invalid priority. Must be one of: {', '.join(valid_priorities)}"

    task_store = MockTaskStore()
    task = task_store.create_task({
        "title": title,
        "description": description or "",
        "priority": priority,
        "due_date": due_date,
    })

    return (
        f"✅ Task created successfully!\n\n"
        f"📌 Title: {title}\n"
        f"🔔 Priority: {priority.upper()}\n"
        f"📅 Due Date: {due_date or 'Not set'}\n"
        f"🆔 Task ID: {task['id']}"
    )

@tool
def list_tasks(filter_status: Optional[Literal["pending", "in_progress", "completed"]] = None) -> str:
    """List all tasks, optionally filtered by status."""
    task_store = MockTaskStore()
    tasks = task_store.get_all(filter_status)

    if not tasks:
        status_msg = f" with status '{filter_status}'" if filter_status else ""
        return f"No tasks found{status_msg}"

    output = f"📋 Tasks ({len(tasks)} found"
    if filter_status:
        output += f", status: {filter_status}"
    output += "):\n\n"

    for t in tasks:
        status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(t["status"], "📌")
        due = f" | Due: {t.get('due_date', 'N/A')}" if t.get('due_date') else ""
        output += (
            f"{status_emoji} {t['title']}\n"
            f"   Status: {t['status']} | Priority: {t['priority']}{due}\n"
            f"   ID: {t['id']}\n\n"
        )

    return output

@tool
def update_task(
    task_id: str,
    status: Optional[Literal["pending", "in_progress", "completed"]] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
) -> str:
    """Update an existing task."""
    task_store = MockTaskStore()

    updates = {}
    if status:
        updates["status"] = status
    if priority:
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            return f"❌ Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        updates["priority"] = priority
    if due_date:
        updates["due_date"] = due_date

    if not updates:
        return "❌ No updates provided"

    task = task_store.update_task(task_id, updates)

    if not task:
        return f"❌ Task not found: {task_id}"

    return (
        f"✅ Task updated successfully!\n\n"
        f"🆔 Task ID: {task['id']}\n"
        f"📌 Title: {task['title']}\n"
        f"🔄 Status: {task['status']}\n"
        f"🔔 Priority: {task['priority']}\n"
        f"📅 Due Date: {task.get('due_date', 'Not set')}"
    )
