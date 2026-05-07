"""
Office Agent Tools - Task Management Module
任务管理工具集
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field


# ==================== Enums ====================

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ==================== Tool Input Schemas ====================

class CreateTaskInput(BaseModel):
    """创建任务输入参数"""
    title: str = Field(description="任务标题")
    description: Optional[str] = Field(default=None, description="任务描述")
    due_date: Optional[str] = Field(default=None, description="截止日期 (YYYY-MM-DD)")
    priority: str = Field(default="medium", description="优先级: low, medium, high, urgent")
    tags: Optional[List[str]] = Field(default=None, description="任务标签")


class UpdateTaskInput(BaseModel):
    """更新任务输入参数"""
    task_id: str = Field(description="任务ID")
    title: Optional[str] = Field(default=None, description="新标题")
    description: Optional[str] = Field(default=None, description="新描述")
    status: Optional[str] = Field(default=None, description="新状态: pending, in_progress, completed, cancelled")
    priority: Optional[str] = Field(default=None, description="新优先级")
    due_date: Optional[str] = Field(default=None, description="新截止日期")


class FilterTasksInput(BaseModel):
    """筛选任务输入参数"""
    status: Optional[str] = Field(default=None, description="按状态筛选")
    priority: Optional[str] = Field(default=None, description="按优先级筛选")
    tag: Optional[str] = Field(default=None, description="按标签筛选")
    due_before: Optional[str] = Field(default=None, description="截止日期早于此日期")
    assignee: Optional[str] = Field(default=None, description="负责人")


# ==================== Mock Task Store ====================

class MockTaskStore:
    """模拟任务存储"""
    
    def __init__(self):
        self.tasks = [
            {
                "id": "task_001",
                "title": "完成项目报告",
                "description": "编写Q1季度项目进度报告",
                "status": "in_progress",
                "priority": "high",
                "created_at": "2025-01-10 09:00",
                "due_date": "2025-01-20",
                "tags": ["report", "Q1"],
                "assignee": "assistant@company.com",
                "subtasks": []
            },
            {
                "id": "task_002",
                "title": "代码评审",
                "description": "评审新功能代码",
                "status": "pending",
                "priority": "medium",
                "created_at": "2025-01-12 14:30",
                "due_date": "2025-01-18",
                "tags": ["coding", "review"],
                "assignee": "assistant@company.com",
                "subtasks": [
                    {"id": "sub_001", "title": "检查代码风格", "done": False},
                    {"id": "sub_002", "title": "验证功能逻辑", "done": False}
                ]
            },
            {
                "id": "task_003",
                "title": "准备演示文稿",
                "description": "为客户演示准备PPT",
                "status": "completed",
                "priority": "high",
                "created_at": "2025-01-08 10:00",
                "due_date": "2025-01-15",
                "tags": ["presentation"],
                "assignee": "assistant@company.com",
                "subtasks": []
            }
        ]
        self.next_id = 4
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        return None
    
    def create_task(self, data: Dict) -> Dict:
        task = {
            "id": f"task_{self.next_id:03d}",
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "assignee": "assistant@company.com",
            "subtasks": [],
            **data
        }
        self.tasks.append(task)
        self.next_id += 1
        return task
    
    def update_task(self, task_id: str, updates: Dict) -> Optional[Dict]:
        for t in self.tasks:
            if t["id"] == task_id:
                t.update(updates)
                return t
        return None
    
    def delete_task(self, task_id: str) -> bool:
        for i, t in enumerate(self.tasks):
            if t["id"] == task_id:
                self.tasks.pop(i)
                return True
        return False
    
    def filter_tasks(self, status: Optional[str] = None, priority: Optional[str] = None,
                    tag: Optional[str] = None, due_before: Optional[str] = None,
                    assignee: Optional[str] = None) -> List[Dict]:
        results = self.tasks
        
        if status:
            results = [t for t in results if t["status"] == status]
        if priority:
            results = [t for t in results if t["priority"] == priority]
        if tag:
            results = [t for t in results if tag in t.get("tags", [])]
        if due_before:
            results = [t for t in results if t.get("due_date") and t["due_date"] <= due_before]
        if assignee:
            results = [t for t in results if t["assignee"] == assignee]
        
        return results


# 全局任务存储实例
_task_store = MockTaskStore()


# ==================== Task Tools ====================

@tool(args_schema=CreateTaskInput, return_direct=True)
def create_task(
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: str = "medium",
    tags: Optional[List[str]] = None
) -> str:
    """
    创建新任务。
    
    当用户需要创建新的待办事项、工作任务或计划时使用此工具。
    
    Args:
        title: 任务标题
        description: 任务详细描述
        due_date: 截止日期，格式 YYYY-MM-DD
        priority: 优先级 (low/medium/high/urgent)
        tags: 任务标签列表
    
    Returns:
        创建结果
    """
    try:
        priority_emoji = {
            "low": "🔵",
            "medium": "🟡",
            "high": "🟠",
            "urgent": "🔴"
        }
        
        task = _task_store.create_task({
            "title": title,
            "description": description or "",
            "due_date": due_date,
            "priority": priority,
            "tags": tags or []
        })
        
        result = f"""✅ 任务创建成功！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 标题: {title}
📝 描述: {description or '无'}
📅 截止日期: {due_date or '未设置'}
🔔 优先级: {priority_emoji.get(priority, '🟡')} {priority.upper()}
🏷️ 标签: {', '.join(tags) if tags else '无'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 任务ID: {task['id']}
"""
        
        return result
        
    except Exception as e:
        return f"❌ 创建任务失败: {str(e)}"


@tool(args_schema=UpdateTaskInput, return_direct=True)
def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None
) -> str:
    """
    更新任务信息。
    
    当用户需要修改任务的标题、描述、状态、优先级或截止日期时使用此工具。
    
    Args:
        task_id: 任务ID
        title: 新标题
        description: 新描述
        status: 新状态 (pending/in_progress/completed/cancelled)
        priority: 新优先级
        due_date: 新截止日期
    
    Returns:
        更新结果
    """
    try:
        task = _task_store.get_task(task_id)
        
        if not task:
            return f"❌ 未找到任务: {task_id}"
        
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status
        if priority is not None:
            updates["priority"] = priority
        if due_date is not None:
            updates["due_date"] = due_date
        
        _task_store.update_task(task_id, updates)
        
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌"
        }
        
        result = f"""✅ 任务已更新！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if title:
            result += f"📌 标题: {title}\n"
        if description is not None:
            result += f"📝 描述: {description or '无'}\n"
        if status:
            result += f"📊 状态: {status_emoji.get(status, '')} {status}\n"
        if priority:
            result += f"🔔 优先级: {priority}\n"
        if due_date:
            result += f"📅 截止日期: {due_date}\n"
        
        result += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 任务ID: {task_id}
"""
        
        return result
        
    except Exception as e:
        return f"❌ 更新任务失败: {str(e)}"


@tool(return_direct=False)
def complete_task(task_id: str) -> str:
    """
    将任务标记为已完成。
    
    当用户完成任务后，需要将任务状态改为已完成时使用此工具。
    
    Args:
        task_id: 任务ID
    
    Returns:
        更新结果
    """
    try:
        task = _task_store.get_task(task_id)
        
        if not task:
            return f"❌ 未找到任务: {task_id}"
        
        _task_store.update_task(task_id, {"status": "completed"})
        
        return f"""✅ 任务已完成！

📌 {task['title']}
🆔 任务ID: {task_id}

🎉 恭喜！又完成了一项任务！"""        
        
    except Exception as e:
        return f"❌ 更新任务失败: {str(e)}"


@tool(args_schema=FilterTasksInput, return_direct=False)
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
    due_before: Optional[str] = None,
    assignee: Optional[str] = None
) -> str:
    """
    列出任务列表。
    
    当用户想查看任务列表、筛选特定条件的任务时使用此工具。
    
    Args:
        status: 按状态筛选 (pending/in_progress/completed/cancelled)
        priority: 按优先级筛选 (low/medium/high/urgent)
        tag: 按标签筛选
        due_before: 截止日期早于此日期
        assignee: 负责人邮箱
    
    Returns:
        任务列表
    """
    try:
        tasks = _task_store.filter_tasks(status, priority, tag, due_before, assignee)
        
        if not tasks:
            filters = []
            if status:
                filters.append(f"状态={status}")
            if priority:
                filters.append(f"优先级={priority}")
            if tag:
                filters.append(f"标签={tag}")
            if due_before:
                filters.append(f"截止日期<{due_before}")
            
            filter_str = ", ".join(filters) if filters else "全部"
            return f"📋 没有找到符合条件的任务\n\n筛选条件: {filter_str}"
        
        # 按状态和优先级排序
        status_order = {"in_progress": 0, "pending": 1, "completed": 2, "cancelled": 3}
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        
        tasks = sorted(tasks, key=lambda x: (
            status_order.get(x["status"], 9),
            priority_order.get(x["priority"], 9)
        ))
        
        # 统计
        status_counts = {}
        for t in self.tasks if hasattr(self, 'tasks') else tasks:
            s = t["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        
        result = f"""📋 任务列表

共 {len(tasks)} 个任务
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        current_status = None
        for t in tasks:
            if t["status"] != current_status:
                current_status = t["status"]
                status_names = {
                    "pending": "⏳ 待处理",
                    "in_progress": "🔄 进行中",
                    "completed": "✅ 已完成",
                    "cancelled": "❌ 已取消"
                }
                result += f"\n### {status_names.get(current_status, current_status)}\n\n"
            
            priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🟠", "urgent": "🔴"}
            emoji = priority_emoji.get(t["priority"], "🟡")
            
            result += f"• {emoji} {t['title']}\n"
            result += f"  ID: {t['id']}"
            if t.get("due_date"):
                result += f" | 截止: {t['due_date']}"
            if t.get("tags"):
                result += f" | 标签: {', '.join(t['tags'])}"
            result += "\n\n"
        
        return result.strip()
        
    except Exception as e:
        return f"❌ 查询任务失败: {str(e)}"


@tool(return_direct=False)
def get_task_detail(task_id: str) -> str:
    """
    获取任务详情。
    
    当用户想查看某个任务的完整信息时使用此工具。
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务详情
    """
    try:
        task = _task_store.get_task(task_id)
        
        if not task:
            return f"❌ 未找到任务: {task_id}"
        
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌"
        }
        
        priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🟠", "urgent": "🔴"}
        
        result = f"""📋 任务详情

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 ID: {task['id']}
📌 标题: {task['title']}
📝 描述: {task.get('description') or '无'}
📊 状态: {status_emoji.get(task['status'], '')} {task['status']}
🔔 优先级: {priority_emoji.get(task['priority'], '🟡')} {task['priority'].upper()}
📅 创建时间: {task['created_at']}
📅 截止日期: {task.get('due_date') or '未设置'}
👤 负责人: {task.get('assignee', '未分配')}
🏷️ 标签: {', '.join(task.get('tags', [])) or '无'}
"""
        
        # 子任务
        if task.get("subtasks"):
            result += "\n📋 子任务:\n"
            for i, st in enumerate(task["subtasks"], 1):
                done_mark = "✅" if st.get("done") else "⬜"
                result += f"   {done_mark} {i}. {st['title']}\n"
        
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return result
        
    except Exception as e:
        return f"❌ 查询任务失败: {str(e)}"


@tool(return_direct=False)
def delete_task(task_id: str) -> str:
    """
    删除任务。
    
    当用户需要永久删除某个任务时使用此工具。
    
    Args:
        task_id: 任务ID
    
    Returns:
        删除结果
    """
    try:
        task = _task_store.get_task(task_id)
        
        if not task:
            return f"❌ 未找到任务: {task_id}"
        
        _task_store.delete_task(task_id)
        
        return f"""✅ 任务已删除

📌 {task['title']}
🆔 任务ID: {task_id}"""        
        
    except Exception as e:
        return f"❌ 删除任务失败: {str(e)}"


@tool(return_direct=False)
def get_my_tasks() -> str:
    """
    获取分配给我的所有任务。
    
    当用户想查看自己负责的所有任务时使用此工具。
    
    Returns:
        任务列表
    """
    try:
        tasks = _task_store.filter_tasks(assignee="assistant@company.com")
        
        if not tasks:
            return "📋 您当前没有分配的任务"
        
        # 按状态分组
        by_status = {
            "in_progress": [],
            "pending": [],
            "completed": []
        }
        
        for t in tasks:
            status = t["status"]
            if status in by_status:
                by_status[status].append(t)
        
        result = "📋 我的任务\n\n"
        
        if by_status["in_progress"]:
            result += f"🔄 进行中 ({len(by_status['in_progress'])}项)\n"
            for t in by_status["in_progress"]:
                result += f"   • {t['title']} (ID: {t['id']})\n"
            result += "\n"
        
        if by_status["pending"]:
            result += f"⏳ 待处理 ({len(by_status['pending'])}项)\n"
            for t in by_status["pending"]:
                due = f" | 截止: {t['due_date']}" if t.get("due_date") else ""
                result += f"   • {t['title']}{due} (ID: {t['id']})\n"
            result += "\n"
        
        if by_status["completed"]:
            result += f"✅ 已完成 ({len(by_status['completed'])})"
        
        return result.strip()
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


@tool(return_direct=False)
def get_overdue_tasks() -> str:
    """
    获取已过期的任务。
    
    当用户想查看已超过截止日期但未完成的任务时使用此工具。
    
    Returns:
        过期任务列表
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        all_tasks = _task_store.tasks
        
        overdue = []
        for t in all_tasks:
            if t["status"] in ["pending", "in_progress"]:
                if t.get("due_date") and t["due_date"] < today:
                    overdue.append(t)
        
        if not overdue:
            return "🎉 太棒了！您没有已过期的任务！"
        
        result = f"""⚠️ 过期任务提醒

共 {len(overdue)} 个任务已过期
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for t in overdue:
            days_late = (datetime.strptime(today, "%Y-%m-%d") - 
                        datetime.strptime(t["due_date"], "%Y-%m-%d")).days
            result += f"🔴 {t['title']}\n"
            result += f"   截止: {t['due_date']} (已过期 {days_late} 天)\n"
            result += f"   ID: {t['id']}\n\n"
        
        return result.strip()
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


# ==================== Tool Exports ====================

TASK_TOOLS = [
    create_task,
    update_task,
    complete_task,
    list_tasks,
    get_task_detail,
    delete_task,
    get_my_tasks,
    get_overdue_tasks
]

__all__ = [
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
    "TaskPriority"
]
