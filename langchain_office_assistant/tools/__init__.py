"""Tools module - Office assistant tools built with LangChain @tool decorator."""

from langchain_core.tools import tool, BaseTool

from typing import List, Optional, Literal
from datetime import datetime


# ==================== Email Tools ====================

class MockEmailStore:
    """Mock email data store."""

    def __init__(self):
        self.emails = [
            {
                "id": "email_001",
                "folder": "inbox",
                "from": "zhangsan@company.com",
                "to": ["assistant@company.com"],
                "subject": "项目进度汇报",
                "body": "本周项目进度如下：\n1. 前端开发完成 80%\n2. 后端 API 联调中",
                "date": "2025-01-14 10:30",
                "read": True
            },
            {
                "id": "email_002",
                "folder": "inbox",
                "from": "lisi@company.com",
                "to": ["assistant@company.com"],
                "subject": "周五会议通知",
                "body": "本周五下午3点有产品评审会议，请准时参加。",
                "date": "2025-01-13 14:20",
                "read": False
            }
        ]
        self.next_id = 3

    def send(self, to: List[str], subject: str, body: str) -> dict:
        new_email = {
            "id": f"email_{self.next_id:03d}",
            "folder": "sent",
            "from": "assistant@company.com",
            "to": to,
            "subject": subject,
            "body": body,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "read": True
        }
        self.emails.append(new_email)
        self.next_id += 1
        return new_email

    def search(self, keyword: str, max_results: int = 10) -> List[dict]:
        results = []
        for email in self.emails:
            if keyword.lower() in email["subject"].lower() or keyword.lower() in email["body"].lower():
                results.append(email)
                if len(results) >= max_results:
                    break
        return results

    def get_email(self, email_id: str) -> Optional[dict]:
        for email in self.emails:
            if email["id"] == email_id:
                return email
        return None


_email_store = MockEmailStore()


@tool
def send_email(
    to: List[str],
    subject: str,
    body: str,
) -> str:
    """Send an email to specified recipients.

    Use this tool when the user wants to send an email to colleagues or contacts.

    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content

    Returns:
        A confirmation message with email details
    """
    try:
        email = _email_store.send(to, subject, body)
        return (
            f"✅ Email sent successfully!\n\n"
            f"To: {', '.join(to)}\n"
            f"Subject: {subject}\n"
            f"Email ID: {email['id']}"
        )
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"


@tool
def search_emails(keyword: str, max_results: int = 10) -> str:
    """Search emails by keyword.

    Use this tool when the user wants to find emails containing specific keywords.

    Args:
        keyword: Search keyword to match in email subjects and bodies
        max_results: Maximum number of results to return (default: 10)

    Returns:
        List of matching emails with details
    """
    try:
        results = _email_store.search(keyword, max_results)

        if not results:
            return f"No emails found matching '{keyword}'"

        output = f"Found {len(results)} email(s):\n\n"
        for email in results:
            read_status = "✓" if email.get("read", False) else "○"
            preview = email['body'][:100] if len(email['body']) > 100 else email['body']
            output += (
                f"📧 [{read_status}] {email['subject']}\n"
                f"   From: {email['from']} | {email['date']}\n"
                f"   Preview: {preview}...\n\n"
            )

        return output
    except Exception as e:
        return f"❌ Search failed: {str(e)}"


@tool
def read_email(email_id: str) -> str:
    """Read a specific email by ID.

    Use this tool when the user wants to read the full content of a specific email.

    Args:
        email_id: The email ID (e.g., 'email_001')

    Returns:
        Full email content
    """
    try:
        email = _email_store.get_email(email_id)

        if not email:
            return f"❌ Email not found: {email_id}"

        email["read"] = True

        cc_str = f"\n📑 CC: {', '.join(email['cc'])}" if email.get('cc') else ""

        return (
            f"📧 Email Details\n"
            f"{'='*50}\n"
            f"Subject: {email['subject']}\n"
            f"From: {email['from']}\n"
            f"To: {', '.join(email['to'])}{cc_str}\n"
            f"Date: {email['date']}\n"
            f"{'='*50}\n\n"
            f"{email['body']}"
        )
    except Exception as e:
        return f"❌ Failed to read email: {str(e)}"


# ==================== Calendar Tools ====================

class MockCalendarStore:
    """Mock calendar data store."""

    def __init__(self):
        self.meetings = [
            {
                "id": "meet_001",
                "title": "产品评审会议",
                "date": "2025-01-15",
                "time": "10:00",
                "duration": 60,
                "participants": ["zhangsan@company.com", "lisi@company.com"],
                "location": "3号会议室",
                "status": "confirmed"
            },
            {
                "id": "meet_002",
                "title": "团队周会",
                "date": "2025-01-15",
                "time": "14:00",
                "duration": 45,
                "participants": ["team@company.com"],
                "location": "线上会议",
                "status": "confirmed"
            }
        ]
        self.next_id = 3

    def get_meetings(self, date: str) -> List[dict]:
        return [m for m in self.meetings if m["date"] == date]

    def create_meeting(self, data: dict) -> dict:
        meeting = {
            "id": f"meet_{self.next_id:03d}",
            "status": "confirmed",
            **data
        }
        self.meetings.append(meeting)
        self.next_id += 1
        return meeting


_calendar_store = MockCalendarStore()


@tool
def check_calendar(date: str) -> str:
    """Check calendar schedule for a specific date.

    Use this tool when the user wants to see what meetings are scheduled on a particular day.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        List of meetings scheduled for that day
    """
    try:
        meetings = _calendar_store.get_meetings(date)

        if not meetings:
            return f"No meetings scheduled for {date}"

        output = f"📅 Meetings on {date}:\n\n"
        for m in meetings:
            output += (
                f"🕐 {m['time']} - {m['title']}\n"
                f"   Duration: {m['duration']} minutes | Location: {m['location']}\n"
                f"   Attendees: {', '.join(m['participants'])}\n\n"
            )

        return output
    except Exception as e:
        return f"❌ Failed to check calendar: {str(e)}"


@tool
def schedule_meeting(
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    participants: List[str],
    location: Optional[str] = None,
) -> str:
    """Schedule a new meeting.

    Use this tool when the user wants to create a new meeting or appointment.

    Args:
        title: Meeting title
        date: Meeting date in YYYY-MM-DD format
        time: Meeting time in HH:MM format
        duration_minutes: Meeting duration in minutes
        participants: List of participant email addresses
        location: Optional meeting location

    Returns:
        Confirmation with meeting details
    """
    try:
        meeting = _calendar_store.create_meeting({
            "title": title,
            "date": date,
            "time": time,
            "duration": duration_minutes,
            "participants": participants,
            "location": location or "Online"
        })

        return (
            f"✅ Meeting scheduled successfully!\n\n"
            f"📌 Title: {title}\n"
            f"📅 Date: {date} at {time}\n"
            f"⏱️ Duration: {duration_minutes} minutes\n"
            f"📍 Location: {location or 'Online'}\n"
            f"👥 Attendees: {', '.join(participants)}\n"
            f"🆔 Meeting ID: {meeting['id']}"
        )
    except Exception as e:
        return f"❌ Failed to schedule meeting: {str(e)}"


# ==================== Task Tools ====================

class MockTaskStore:
    """Mock task data store."""

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


_task_store = MockTaskStore()


@tool
def create_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[str] = None,
) -> str:
    """Create a new task.

    Use this tool when the user wants to create a new todo item or task.

    Args:
        title: Task title
        description: Optional task description
        priority: Task priority (low, medium, high, urgent)
        due_date: Optional due date in YYYY-MM-DD format

    Returns:
        Confirmation with task details
    """
    try:
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            return f"❌ Invalid priority. Must be one of: {', '.join(valid_priorities)}"

        task = _task_store.create_task({
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
    except Exception as e:
        return f"❌ Failed to create task: {str(e)}"


@tool
def list_tasks(filter_status: Optional[Literal["pending", "in_progress", "completed"]] = None) -> str:
    """List all tasks, optionally filtered by status.

    Use this tool when the user wants to see their tasks or todos.

    Args:
        filter_status: Optional filter by status (pending, in_progress, completed)

    Returns:
        List of tasks matching the filter
    """
    try:
        tasks = _task_store.get_all(filter_status)

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
    except Exception as e:
        return f"❌ Failed to list tasks: {str(e)}"


# ==================== Document Tools ====================

@tool
def search_documents(keyword: str) -> str:
    """Search documents for a keyword.

    Use this tool when the user wants to find documents containing specific text.

    Args:
        keyword: Keyword to search for in documents

    Returns:
        List of matching documents
    """
    try:
        return (
            f"🔍 Search results for '{keyword}':\n\n"
            f"Found 2 documents:\n\n"
            f"1. 📄 documents/project_report.md\n"
            f"   Preview: Contains '{keyword}' in section 2...\n\n"
            f"2. 📄 documents/meeting_notes.txt\n"
            f"   Preview: Mentions '{keyword}' in action items..."
        )
    except Exception as e:
        return f"❌ Search failed: {str(e)}"


@tool
def summarize_document(file_path: str) -> str:
    """Summarize a document's key points.

    Use this tool when the user wants a quick summary of a document.

    Args:
        file_path: Path to the document file

    Returns:
        Summary of the document's key points
    """
    try:
        return (
            f"📄 Document Summary: {file_path}\n\n"
            f"Key Points:\n"
            f"1. Main topic covered in the document\n"
            f"2. Important conclusions reached\n"
            f"3. Action items or recommendations\n\n"
            f"Total length: ~500 words\n"
            f"Sections: 4"
        )
    except Exception as e:
        return f"❌ Failed to summarize document: {str(e)}"


# ==================== Export All Tools ====================

EMAIL_TOOLS: List[BaseTool] = [send_email, search_emails, read_email]
CALENDAR_TOOLS: List[BaseTool] = [check_calendar, schedule_meeting]
TASK_TOOLS: List[BaseTool] = [create_task, list_tasks]
DOCUMENT_TOOLS: List[BaseTool] = [search_documents, summarize_document]

ALL_OFFICE_TOOLS: List[BaseTool] = (
    EMAIL_TOOLS +
    CALENDAR_TOOLS +
    TASK_TOOLS +
    DOCUMENT_TOOLS
)


__all__ = [
    "send_email",
    "search_emails",
    "read_email",
    "check_calendar",
    "schedule_meeting",
    "create_task",
    "list_tasks",
    "search_documents",
    "summarize_document",
    "EMAIL_TOOLS",
    "CALENDAR_TOOLS",
    "TASK_TOOLS",
    "DOCUMENT_TOOLS",
    "ALL_OFFICE_TOOLS",
]
