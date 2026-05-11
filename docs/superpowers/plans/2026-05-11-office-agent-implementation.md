# Office Agent 办公智能体实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 LangChain + LangGraph 的插件化办公智能体系统，支持邮件管理、日历调度、任务管理、文档处理、PPT生成、知识库检索、图表报告和计算追溯等功能。

**Architecture:** 插件化架构，核心智能体通过统一接口管理多个功能插件，支持 REST API 和 CLI 两种调用方式，数据层使用向量数据库和关系数据库存储。

**Tech Stack:** LangChain, LangGraph, FastAPI, python-docx, openpyxl, PyPDF2, python-pptx, matplotlib, plotly, Milvus/Qdrant, Redis

---

## 目录结构规划

```
langchain_office_assistant/
├── agents/                    # 智能体核心
│   ├── __init__.py
│   ├── core.py                # 智能体核心逻辑
│   ├── intent_recognizer.py   # 意图识别
│   ├── plan_executor.py       # 计划执行器
│   ├── memory_manager.py      # 记忆管理
│   └── trace_recorder.py      # 追溯记录器
├── plugins/                   # 插件系统
│   ├── __init__.py
│   ├── base.py                # 插件基类
│   ├── email/                 # 邮件插件
│   ├── calendar/              # 日历插件
│   ├── task/                  # 任务插件
│   ├── document/              # 文档插件
│   ├── ppt/                   # PPT插件
│   ├── knowledge/             # 知识库插件
│   ├── chart/                 # 图表插件
│   └── calc/                  # 计算插件
├── tools/                     # 工具封装
│   ├── __init__.py
│   └── registry.py            # 工具注册中心
├── utils/                     # 工具函数
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── logger.py              # 日志管理
│   └── helpers.py             # 辅助函数
├── data/                      # 数据层
│   ├── __init__.py
│   ├── vector_db.py           # 向量数据库
│   └── file_store.py          # 文件存储
├── api/                       # API服务
│   ├── __init__.py
│   ├── main.py                # FastAPI入口
│   ├── endpoints/             # API端点
│   └── dependencies.py        # 依赖注入
├── cli/                       # 命令行接口
│   ├── __init__.py
│   └── main.py
├── tests/                     # 测试用例
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 任务分解

### Task 1: 项目初始化与基础配置

**Files:**
- Create: `langchain_office_assistant/pyproject.toml`
- Create: `langchain_office_assistant/requirements.txt`
- Create: `langchain_office_assistant/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "langchain-office-assistant"
version = "1.0.0"
description = "Office automation agent built on LangChain + LangGraph"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.1.0",
    "langchain-core>=0.1.0",
    "langchain-community>=0.1.0",
    "langgraph>=0.1.0",
    "langchain-openai>=0.1.0",
    "langchain-ollama>=0.1.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
    "pydantic>=2.0.0",
    "python-docx>=0.8.11",
    "openpyxl>=3.0.0",
    "PyPDF2>=3.0.0",
    "python-pptx>=0.6.21",
    "matplotlib>=3.7.0",
    "plotly>=5.15.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "redis>=5.0.0",
    "python-dotenv>=1.0.0",
    "icalendar>=4.0.0",
]

[project.scripts]
office-agent = "langchain_office_assistant.cli.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create requirements.txt**

```txt
langchain>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.1.0
langgraph>=0.1.0
langchain-openai>=0.1.0
langchain-ollama>=0.1.0
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
python-docx>=0.8.11
openpyxl>=3.0.0
PyPDF2>=3.0.0
python-pptx>=0.6.21
matplotlib>=3.7.0
plotly>=5.15.0
pandas>=2.0.0
numpy>=1.24.0
redis>=5.0.0
python-dotenv>=1.0.0
icalendar>=4.0.0
```

- [ ] **Step 3: Create root __init__.py**

```python
__version__ = "1.0.0"
__author__ = "Office Agent Team"

from langchain_office_assistant.agents import (
    OfficeAgent,
    create_office_agent,
    run_office_assistant,
)

from langchain_office_assistant.plugins import (
    EmailPlugin,
    CalendarPlugin,
    TaskPlugin,
    DocumentPlugin,
    PPTPlugin,
    KnowledgePlugin,
    ChartPlugin,
    CalcPlugin,
)

__all__ = [
    "__version__",
    "__author__",
    "OfficeAgent",
    "create_office_agent",
    "run_office_assistant",
    "EmailPlugin",
    "CalendarPlugin",
    "TaskPlugin",
    "DocumentPlugin",
    "PPTPlugin",
    "KnowledgePlugin",
    "ChartPlugin",
    "CalcPlugin",
]
```

- [ ] **Step 4: Install dependencies**

```bash
cd /workspace/langchain_office_assistant
pip install -e .
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml requirements.txt __init__.py
git commit -m "feat: initialize project structure"
```

---

### Task 2: 工具函数模块

**Files:**
- Create: `langchain_office_assistant/utils/__init__.py`
- Create: `langchain_office_assistant/utils/config.py`
- Create: `langchain_office_assistant/utils/logger.py`
- Create: `langchain_office_assistant/utils/helpers.py`

- [ ] **Step 1: Create utils/__init__.py**

```python
from langchain_office_assistant.utils.config import Config
from langchain_office_assistant.utils.logger import get_logger
from langchain_office_assistant.utils.helpers import (
    format_datetime,
    validate_email,
    generate_session_id,
)

__all__ = [
    "Config",
    "get_logger",
    "format_datetime",
    "validate_email",
    "generate_session_id",
]
```

- [ ] **Step 2: Create utils/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    agent_model: str = "gpt-4"
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    redis_url: str = "redis://localhost:6379"
    vector_db_url: str = "http://localhost:19530"
    vector_db_type: str = "milvus"
    
    log_level: str = "INFO"
    debug_mode: bool = False
    
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

config = Config()
```

- [ ] **Step 3: Create utils/logger.py**

```python
import logging
from typing import Optional
from langchain_office_assistant.utils.config import config

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    log_level = level or config.log_level
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
```

- [ ] **Step 4: Create utils/helpers.py**

```python
from datetime import datetime
import re
import uuid

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(format)

def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def generate_session_id() -> str:
    return str(uuid.uuid4())

def parse_date(date_str: str) -> datetime:
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")
```

- [ ] **Step 5: Commit**

```bash
git add utils/
git commit -m "feat: add utility functions"
```

---

### Task 3: 插件基类定义

**Files:**
- Create: `langchain_office_assistant/plugins/__init__.py`
- Create: `langchain_office_assistant/plugins/base.py`

- [ ] **Step 1: Create plugins/__init__.py**

```python
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
```

- [ ] **Step 2: Create plugins/base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Any, Dict
from langchain_core.tools import BaseTool

class BasePlugin(ABC):
    name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    
    def __init__(self):
        self.tools: List[BaseTool] = []
    
    @abstractmethod
    def initialize(self, config: Dict) -> None:
        """初始化插件"""
    
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """获取插件提供的工具列表"""
    
    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具调用"""
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "tools": [t.name for t in self.get_tools()],
        }
```

- [ ] **Step 3: Commit**

```bash
git add plugins/__init__.py plugins/base.py
git commit -m "feat: add plugin base class"
```

---

### Task 4: 邮件插件

**Files:**
- Create: `langchain_office_assistant/plugins/email/__init__.py`
- Create: `langchain_office_assistant/plugins/email/plugin.py`

- [ ] **Step 1: Create email/__init__.py**

```python
from langchain_office_assistant.plugins.email.plugin import EmailPlugin

__all__ = ["EmailPlugin"]
```

- [ ] **Step 2: Create email/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
from langchain_office_assistant.utils.helpers import validate_email
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime

logger = get_logger(__name__)

class MockEmailStore:
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
        for email_item in self.emails:
            if keyword.lower() in email_item["subject"].lower() or keyword.lower() in email_item["body"].lower():
                results.append(email_item)
                if len(results) >= max_results:
                    break
        return results
    
    def get_email(self, email_id: str) -> Optional[dict]:
        for email_item in self.emails:
            if email_item["id"] == email_id:
                return email_item
        return None

class EmailPlugin(BasePlugin):
    name = "email"
    description = "邮件管理插件 - 发送、搜索、阅读邮件"
    
    def __init__(self):
        super().__init__()
        self.email_store = MockEmailStore()
        self.config = {}
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"EmailPlugin initialized with config: {config}")
    
    def get_tools(self) -> List:
        return [send_email, search_emails, read_email]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "send_email": send_email,
            "search_emails": search_emails,
            "read_email": read_email,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def send_email(to: List[str], subject: str, body: str) -> str:
    """Send an email to specified recipients."""
    for email_addr in to:
        if not validate_email(email_addr):
            return f"❌ Invalid email address: {email_addr}"
    
    email_store = MockEmailStore()
    email_result = email_store.send(to, subject, body)
    
    return (
        f"✅ Email sent successfully!\n\n"
        f"To: {', '.join(to)}\n"
        f"Subject: {subject}\n"
        f"Email ID: {email_result['id']}"
    )

@tool
def search_emails(keyword: str, max_results: int = 10) -> str:
    """Search emails by keyword."""
    email_store = MockEmailStore()
    results = email_store.search(keyword, max_results)
    
    if not results:
        return f"No emails found matching '{keyword}'"
    
    output = f"Found {len(results)} email(s):\n\n"
    for email_item in results:
        read_status = "✓" if email_item.get("read", False) else "○"
        preview = email_item['body'][:100] if len(email_item['body']) > 100 else email_item['body']
        output += (
            f"📧 [{read_status}] {email_item['subject']}\n"
            f"   From: {email_item['from']} | {email_item['date']}\n"
            f"   Preview: {preview}...\n\n"
        )
    
    return output

@tool
def read_email(email_id: str) -> str:
    """Read a specific email by ID."""
    email_store = MockEmailStore()
    email_item = email_store.get_email(email_id)
    
    if not email_item:
        return f"❌ Email not found: {email_id}"
    
    email_item["read"] = True
    cc_str = f"\n📑 CC: {', '.join(email_item['cc'])}" if email_item.get('cc') else ""
    
    return (
        f"📧 Email Details\n"
        f"{'='*50}\n"
        f"Subject: {email_item['subject']}\n"
        f"From: {email_item['from']}\n"
        f"To: {', '.join(email_item['to'])}{cc_str}\n"
        f"Date: {email_item['date']}\n"
        f"{'='*50}\n\n"
        f"{email_item['body']}"
    )
```

- [ ] **Step 3: Commit**

```bash
git add plugins/email/
git commit -m "feat: add email plugin"
```

---

### Task 5: 日历插件

**Files:**
- Create: `langchain_office_assistant/plugins/calendar/__init__.py`
- Create: `langchain_office_assistant/plugins/calendar/plugin.py`

- [ ] **Step 1: Create calendar/__init__.py**

```python
from langchain_office_assistant.plugins.calendar.plugin import CalendarPlugin

__all__ = ["CalendarPlugin"]
```

- [ ] **Step 2: Create calendar/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class MockCalendarStore:
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

class CalendarPlugin(BasePlugin):
    name = "calendar"
    description = "日历管理插件 - 查询日程、创建会议"
    
    def __init__(self):
        super().__init__()
        self.calendar_store = MockCalendarStore()
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"CalendarPlugin initialized")
    
    def get_tools(self) -> List:
        return [check_calendar, schedule_meeting]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "check_calendar": check_calendar,
            "schedule_meeting": schedule_meeting,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def check_calendar(date: str) -> str:
    """Check calendar schedule for a specific date."""
    calendar_store = MockCalendarStore()
    meetings = calendar_store.get_meetings(date)
    
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

@tool
def schedule_meeting(
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    participants: List[str],
    location: Optional[str] = None,
) -> str:
    """Schedule a new meeting."""
    calendar_store = MockCalendarStore()
    
    meeting = calendar_store.create_meeting({
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
```

- [ ] **Step 3: Commit**

```bash
git add plugins/calendar/
git commit -m "feat: add calendar plugin"
```

---

### Task 6: 任务插件

**Files:**
- Create: `langchain_office_assistant/plugins/task/__init__.py`
- Create: `langchain_office_assistant/plugins/task/plugin.py`

- [ ] **Step 1: Create task/__init__.py**

```python
from langchain_office_assistant.plugins.task.plugin import TaskPlugin

__all__ = ["TaskPlugin"]
```

- [ ] **Step 2: Create task/plugin.py**

```python
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
    """Update task status, priority, or due date."""
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
```

- [ ] **Step 3: Commit**

```bash
git add plugins/task/
git commit -m "feat: add task plugin"
```

---

### Task 7: 文档插件

**Files:**
- Create: `langchain_office_assistant/plugins/document/__init__.py`
- Create: `langchain_office_assistant/plugins/document/plugin.py`

- [ ] **Step 1: Create document/__init__.py**

```python
from langchain_office_assistant.plugins.document.plugin import DocumentPlugin

__all__ = ["DocumentPlugin"]
```

- [ ] **Step 2: Create document/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
import docx
import openpyxl
from PyPDF2 import PdfReader
import os

logger = get_logger(__name__)

class DocumentPlugin(BasePlugin):
    name = "document"
    description = "文档处理插件 - Word/Excel/PDF读写"
    
    def __init__(self):
        super().__init__()
        self.documents = [
            {
                "id": "doc_001",
                "name": "项目报告.docx",
                "type": "docx",
                "path": "documents/project_report.docx",
                "size": 10240,
                "modified": "2025-01-14"
            },
            {
                "id": "doc_002",
                "name": "会议记录.pdf",
                "type": "pdf",
                "path": "documents/meeting_notes.pdf",
                "size": 5120,
                "modified": "2025-01-13"
            },
            {
                "id": "doc_003",
                "name": "数据报表.xlsx",
                "type": "xlsx",
                "path": "documents/data_report.xlsx",
                "size": 8192,
                "modified": "2025-01-12"
            }
        ]
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"DocumentPlugin initialized")
    
    def get_tools(self) -> List:
        return [search_documents, summarize_document, read_document, write_document]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "search_documents": search_documents,
            "summarize_document": summarize_document,
            "read_document": read_document,
            "write_document": write_document,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def search_documents(keyword: str) -> str:
    """Search documents for a keyword."""
    mock_results = [
        {
            "id": "doc_001",
            "name": "项目报告.docx",
            "type": "docx",
            "preview": f"文档内容包含 '{keyword}' 相关章节..."
        },
        {
            "id": "doc_002", 
            "name": "会议记录.pdf",
            "type": "pdf",
            "preview": f"会议讨论了与 '{keyword}' 相关的内容..."
        }
    ]
    
    output = f"🔍 Search results for '{keyword}':\n\n"
    for doc in mock_results:
        output += (
            f"📄 {doc['name']} ({doc['type']})\n"
            f"   Preview: {doc['preview']}\n"
            f"   ID: {doc['id']}\n\n"
        )
    
    return output

@tool
def summarize_document(file_path: str) -> str:
    """Summarize a document's key points."""
    try:
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'docx':
            doc = docx.Document(file_path)
            content = '\n'.join([p.text for p in doc.paragraphs])
        elif ext == 'pdf':
            reader = PdfReader(file_path)
            content = '\n'.join([page.extract_text() for page in reader.pages])
        elif ext == 'xlsx':
            wb = openpyxl.load_workbook(file_path)
            content = ""
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                content += f"Sheet: {sheet}\n"
                for row in ws.iter_rows(values_only=True):
                    content += f"{row}\n"
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        lines = content.split('\n')[:5]
        preview = '\n'.join(lines)
        
        return (
            f"📄 Document Summary: {file_path}\n\n"
            f"Key Points:\n"
            f"1. Document type: {ext.upper()}\n"
            f"2. Content preview:\n{preview}\n"
            f"3. Full content length: {len(content)} characters\n"
            f"4. Contains {len(content.split())} words"
        )
    except Exception as e:
        return f"❌ Failed to summarize document: {str(e)}"

@tool
def read_document(file_path: str) -> str:
    """Read document content."""
    try:
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'docx':
            doc = docx.Document(file_path)
            content = '\n'.join([p.text for p in doc.paragraphs])
        elif ext == 'pdf':
            reader = PdfReader(file_path)
            content = '\n'.join([page.extract_text() for page in reader.pages])
        elif ext == 'xlsx':
            wb = openpyxl.load_workbook(file_path)
            content = ""
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                content += f"=== Sheet: {sheet} ===\n"
                for row in ws.iter_rows(values_only=True):
                    content += f"{row}\n"
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        return f"📄 Content of {file_path}:\n\n{content}"
    except Exception as e:
        return f"❌ Failed to read document: {str(e)}"

@tool
def write_document(file_path: str, content: str, format: str = "txt") -> str:
    """Write content to a document."""
    try:
        ext = format.lower()
        
        if ext == 'docx':
            doc = docx.Document()
            doc.add_paragraph(content)
            doc.save(file_path)
        elif ext == 'xlsx':
            wb = openpyxl.Workbook()
            ws = wb.active
            for i, line in enumerate(content.split('\n'), 1):
                ws.cell(row=i, column=1, value=line)
            wb.save(file_path)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return f"✅ Document saved successfully!\n\n📄 File: {file_path}\n📊 Format: {format.upper()}"
    except Exception as e:
        return f"❌ Failed to write document: {str(e)}"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/document/
git commit -m "feat: add document plugin"
```

---

### Task 8: PPT插件

**Files:**
- Create: `langchain_office_assistant/plugins/ppt/__init__.py`
- Create: `langchain_office_assistant/plugins/ppt/plugin.py`

- [ ] **Step 1: Create ppt/__init__.py**

```python
from langchain_office_assistant.plugins.ppt.plugin import PPTPlugin

__all__ = ["PPTPlugin"]
```

- [ ] **Step 2: Create ppt/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

logger = get_logger(__name__)

class PPTPlugin(BasePlugin):
    name = "ppt"
    description = "PPT生成插件 - 模板支持、图表嵌入"
    
    def __init__(self):
        super().__init__()
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"PPTPlugin initialized")
    
    def get_tools(self) -> List:
        return [create_ppt, add_slide, add_chart_to_ppt, save_ppt]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "create_ppt": create_ppt,
            "add_slide": add_slide,
            "add_chart_to_ppt": add_chart_to_ppt,
            "save_ppt": save_ppt,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

_ppt_instances = {}

@tool
def create_ppt(title: str, template: Optional[str] = None) -> str:
    """Create a new PowerPoint presentation."""
    try:
        if template:
            prs = Presentation(template)
        else:
            prs = Presentation()
        
        slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(slide_layout)
        title_placeholder = slide.shapes.title
        title_placeholder.text = title
        
        instance_id = f"ppt_{id(prs)}"
        _ppt_instances[instance_id] = prs
        
        return f"✅ PowerPoint presentation created!\n\n📌 Title: {title}\n🆔 Instance ID: {instance_id}"
    except Exception as e:
        return f"❌ Failed to create PPT: {str(e)}"

@tool
def add_slide(
    instance_id: str,
    slide_type: str = "title",
    title: Optional[str] = None,
    content: Optional[str] = None,
    bullet_points: Optional[List[str]] = None
) -> str:
    """Add a slide to an existing presentation."""
    try:
        if instance_id not in _ppt_instances:
            return f"❌ Presentation not found: {instance_id}"
        
        prs = _ppt_instances[instance_id]
        
        layout_map = {
            "title": 0,
            "content": 1,
            "section": 2,
            "title_only": 5,
            "blank": 6,
        }
        
        layout_idx = layout_map.get(slide_type, 1)
        slide_layout = prs.slide_layouts[layout_idx]
        slide = prs.slides.add_slide(slide_layout)
        
        if title:
            if slide.shapes.title:
                slide.shapes.title.text = title
        
        if content:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    if not shape.text or shape == slide.shapes.title:
                        continue
                    shape.text = content
        
        if bullet_points:
            for shape in slide.shapes:
                if shape.has_text_frame and shape != slide.shapes.title:
                    tf = shape.text_frame
                    tf.clear()
                    for point in bullet_points:
                        p = tf.add_paragraph()
                        p.text = point
                        p.level = 0
        
        return f"✅ Slide added successfully!\n\n📄 Slide Type: {slide_type}\n📌 Title: {title or 'N/A'}"
    except Exception as e:
        return f"❌ Failed to add slide: {str(e)}"

@tool
def add_chart_to_ppt(
    instance_id: str,
    chart_type: str = "bar",
    title: str = "Chart",
    categories: List[str] = None,
    values: List[float] = None
) -> str:
    """Add a chart to a presentation."""
    try:
        if instance_id not in _ppt_instances:
            return f"❌ Presentation not found: {instance_id}"
        
        prs = _ppt_instances[instance_id]
        slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(slide_layout)
        
        categories = categories or ["A", "B", "C", "D"]
        values = values or [10, 20, 30, 40]
        
        from pptx.chart.data import CategoryChartData
        from pptx.enum.chart import XL_CHART_TYPE
        
        chart_data = CategoryChartData()
        chart_data.categories = categories
        chart_data.add_series("Values", values)
        
        x, y, cx, cy = Inches(1), Inches(1), Inches(8), Inches(5)
        
        chart_types = {
            "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "pie": XL_CHART_TYPE.PIE,
            "line": XL_CHART_TYPE.LINE,
            "area": XL_CHART_TYPE.AREA,
        }
        
        chart_type_enum = chart_types.get(chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED)
        slide.shapes.add_chart(chart_type_enum, x, y, cx, cy, chart_data)
        
        title_shape = slide.shapes.title
        if title_shape:
            title_shape.text = title
        
        return f"✅ Chart added successfully!\n\n📊 Chart Type: {chart_type}\n📌 Title: {title}"
    except Exception as e:
        return f"❌ Failed to add chart: {str(e)}"

@tool
def save_ppt(instance_id: str, file_path: str) -> str:
    """Save the presentation to a file."""
    try:
        if instance_id not in _ppt_instances:
            return f"❌ Presentation not found: {instance_id}"
        
        prs = _ppt_instances[instance_id]
        prs.save(file_path)
        
        del _ppt_instances[instance_id]
        
        return f"✅ Presentation saved!\n\n📄 File: {file_path}"
    except Exception as e:
        return f"❌ Failed to save PPT: {str(e)}"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/ppt/
git commit -m "feat: add ppt plugin"
```

---

### Task 9: 知识库插件

**Files:**
- Create: `langchain_office_assistant/plugins/knowledge/__init__.py`
- Create: `langchain_office_assistant/plugins/knowledge/plugin.py`

- [ ] **Step 1: Create knowledge/__init__.py**

```python
from langchain_office_assistant.plugins.knowledge.plugin import KnowledgePlugin

__all__ = ["KnowledgePlugin"]
```

- [ ] **Step 2: Create knowledge/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import os

logger = get_logger(__name__)

class KnowledgePlugin(BasePlugin):
    name = "knowledge"
    description = "知识库插件 - 向量检索、多模态支持"
    
    def __init__(self):
        super().__init__()
        self.vector_store = None
        self.documents = []
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        self._init_vector_store()
        logger.info(f"KnowledgePlugin initialized")
    
    def _init_vector_store(self):
        try:
            embeddings = OpenAIEmbeddings(
                api_key=self.config.get("openai_api_key"),
                model="text-embedding-3-small"
            )
            
            if os.path.exists("knowledge_db"):
                self.vector_store = FAISS.load_local(
                    "knowledge_db",
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                self.vector_store = FAISS.from_texts(
                    ["Welcome to the knowledge base"],
                    embeddings
                )
                self.vector_store.save_local("knowledge_db")
        except Exception as e:
            logger.warning(f"Failed to initialize vector store: {e}")
    
    def get_tools(self) -> List:
        return [add_document, search_knowledge, query_knowledge, list_documents]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "add_document": add_document,
            "search_knowledge": search_knowledge,
            "query_knowledge": query_knowledge,
            "list_documents": list_documents,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

_knowledge_instance = None

def _get_knowledge() -> KnowledgePlugin:
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = KnowledgePlugin()
        _knowledge_instance.initialize({})
    return _knowledge_instance

@tool
def add_document(content: str, title: str, metadata: Optional[Dict] = None) -> str:
    """Add a document to the knowledge base."""
    try:
        knowledge = _get_knowledge()
        
        text_splitter = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separator="\n"
        )
        
        chunks = text_splitter.split_text(content)
        
        if knowledge.vector_store:
            for i, chunk in enumerate(chunks):
                chunk_metadata = {"title": title, "chunk": i, **(metadata or {})}
                knowledge.vector_store.add_texts([chunk], metadatas=[chunk_metadata])
            knowledge.vector_store.save_local("knowledge_db")
        
        knowledge.documents.append({
            "title": title,
            "content_length": len(content),
            "chunks": len(chunks),
            "metadata": metadata
        })
        
        return f"✅ Document added successfully!\n\n📄 Title: {title}\n📊 Chunks: {len(chunks)}"
    except Exception as e:
        return f"❌ Failed to add document: {str(e)}"

@tool
def search_knowledge(query: str, top_k: int = 5) -> str:
    """Search the knowledge base for relevant documents."""
    try:
        knowledge = _get_knowledge()
        
        if not knowledge.vector_store:
            return "⚠️ Vector store not initialized"
        
        results = knowledge.vector_store.similarity_search(query, k=top_k)
        
        if not results:
            return f"No results found for '{query}'"
        
        output = f"🔍 Search results for '{query}' ({len(results)} found):\n\n"
        for i, doc in enumerate(results, 1):
            output += (
                f"{i}. 📄 {doc.metadata.get('title', 'Untitled')}\n"
                f"   Relevance: High\n"
                f"   Preview: {doc.page_content[:100]}...\n\n"
            )
        
        return output
    except Exception as e:
        return f"❌ Search failed: {str(e)}"

@tool
def query_knowledge(query: str) -> str:
    """Query the knowledge base and get a direct answer."""
    try:
        knowledge = _get_knowledge()
        
        if not knowledge.vector_store:
            return "⚠️ Vector store not initialized"
        
        from langchain.chains import RetrievalQA
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=knowledge.vector_store.as_retriever()
        )
        
        result = qa_chain.run(query)
        
        return f"🤖 Answer:\n\n{result}"
    except Exception as e:
        return f"❌ Query failed: {str(e)}"

@tool
def list_documents() -> str:
    """List all documents in the knowledge base."""
    try:
        knowledge = _get_knowledge()
        
        if not knowledge.documents:
            return "No documents in knowledge base"
        
        output = f"📚 Documents in knowledge base ({len(knowledge.documents)}):\n\n"
        for i, doc in enumerate(knowledge.documents, 1):
            output += (
                f"{i}. {doc['title']}\n"
                f"   Length: {doc['content_length']} characters\n"
                f"   Chunks: {doc['chunks']}\n\n"
            )
        
        return output
    except Exception as e:
        return f"❌ Failed to list documents: {str(e)}"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/knowledge/
git commit -m "feat: add knowledge plugin"
```

---

### Task 10: 图表插件

**Files:**
- Create: `langchain_office_assistant/plugins/chart/__init__.py`
- Create: `langchain_office_assistant/plugins/chart/plugin.py`

- [ ] **Step 1: Create chart/__init__.py**

```python
from langchain_office_assistant.plugins.chart.plugin import ChartPlugin

__all__ = ["ChartPlugin"]
```

- [ ] **Step 2: Create chart/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np

logger = get_logger(__name__)

class ChartPlugin(BasePlugin):
    name = "chart"
    description = "图表插件 - 折线图、柱状图、雷达图等"
    
    def __init__(self):
        super().__init__()
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        plt.switch_backend('Agg')
        logger.info(f"ChartPlugin initialized")
    
    def get_tools(self) -> List:
        return [create_bar_chart, create_line_chart, create_pie_chart, create_radar_chart, create_scatter_plot]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "create_bar_chart": create_bar_chart,
            "create_line_chart": create_line_chart,
            "create_pie_chart": create_pie_chart,
            "create_radar_chart": create_radar_chart,
            "create_scatter_plot": create_scatter_plot,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def create_bar_chart(
    title: str,
    labels: List[str],
    values: List[float],
    file_path: str = "chart.png",
    color: str = "blue"
) -> str:
    """Create a bar chart."""
    try:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, values, color=color)
        
        plt.title(title, fontsize=14)
        plt.xlabel("Categories", fontsize=12)
        plt.ylabel("Values", fontsize=12)
        plt.xticks(rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Bar chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Categories: {', '.join(labels)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_line_chart(
    title: str,
    x_data: List[str],
    y_data: List[float],
    file_path: str = "chart.png",
    color: str = "blue",
    show_markers: bool = True
) -> str:
    """Create a line chart."""
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(x_data, y_data, color=color, marker='o' if show_markers else None, linewidth=2)
        
        plt.title(title, fontsize=14)
        plt.xlabel("X Axis", fontsize=12)
        plt.ylabel("Y Axis", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Line chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Data points: {len(x_data)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_pie_chart(
    title: str,
    labels: List[str],
    values: List[float],
    file_path: str = "chart.png"
) -> str:
    """Create a pie chart."""
    try:
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title(title, fontsize=14)
        plt.axis('equal')
        
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Pie chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Categories: {', '.join(labels)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_radar_chart(
    title: str,
    categories: List[str],
    values: List[float],
    file_path: str = "chart.png"
) -> str:
    """Create a radar chart."""
    try:
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=title
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2]
                )),
            title=title,
            showlegend=True
        )
        
        pio.write_image(fig, file_path)
        
        return f"✅ Radar chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Dimensions: {len(categories)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_scatter_plot(
    title: str,
    x_data: List[float],
    y_data: List[float],
    file_path: str = "chart.png",
    color: str = "blue"
) -> str:
    """Create a scatter plot."""
    try:
        plt.figure(figsize=(10, 6))
        plt.scatter(x_data, y_data, color=color, s=100, alpha=0.7)
        
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)
        plt.plot(x_data, p(x_data), "r--")
        
        plt.title(title, fontsize=14)
        plt.xlabel("X Values", fontsize=12)
        plt.ylabel("Y Values", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Scatter plot created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Data points: {len(x_data)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/chart/
git commit -m "feat: add chart plugin"
```

---

### Task 11: 计算插件

**Files:**
- Create: `langchain_office_assistant/plugins/calc/__init__.py`
- Create: `langchain_office_assistant/plugins/calc/plugin.py`

- [ ] **Step 1: Create calc/__init__.py**

```python
from langchain_office_assistant.plugins.calc.plugin import CalcPlugin

__all__ = ["CalcPlugin"]
```

- [ ] **Step 2: Create calc/plugin.py**

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
import pandas as pd
import numpy as np
import math
from datetime import datetime

logger = get_logger(__name__)

class CalcPlugin(BasePlugin):
    name = "calc"
    description = "计算插件 - 公式计算、数据统计"
    
    def __init__(self):
        super().__init__()
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"CalcPlugin initialized")
    
    def get_tools(self) -> List:
        return [calculate, statistics, currency_convert, date_diff, unit_convert]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "calculate": calculate,
            "statistics": statistics,
            "currency_convert": currency_convert,
            "date_diff": date_diff,
            "unit_convert": unit_convert,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        allowed_funcs = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'sqrt': math.sqrt,
            'abs': abs,
            'pow': pow,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }
        
        result = eval(expression, {"__builtins__": {}}, allowed_funcs)
        
        return f"🧮 Calculation Result:\n\n{expression} = {result}"
    except Exception as e:
        return f"❌ Calculation failed: {str(e)}"

@tool
def statistics(numbers: List[float]) -> str:
    """Calculate statistics for a list of numbers."""
    try:
        if not numbers:
            return "❌ Empty number list"
        
        arr = np.array(numbers)
        
        stats = {
            "count": len(numbers),
            "sum": np.sum(arr),
            "mean": np.mean(arr),
            "median": np.median(arr),
            "min": np.min(arr),
            "max": np.max(arr),
            "std": np.std(arr),
            "variance": np.var(arr),
        }
        
        output = "📊 Statistics Results:\n\n"
        for key, value in stats.items():
            output += f"• {key}: {value:.2f}\n"
        
        return output
    except Exception as e:
        return f"❌ Statistics calculation failed: {str(e)}"

@tool
def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency amounts."""
    try:
        rates = {
            "USD": 1.0,
            "CNY": 7.24,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 154.0,
            "KRW": 1380.0,
            "AUD": 1.54,
            "CAD": 1.36,
        }
        
        from_rate = rates.get(from_currency.upper())
        to_rate = rates.get(to_currency.upper())
        
        if not from_rate or not to_rate:
            return f"❌ Unsupported currency. Supported: {', '.join(rates.keys())}"
        
        result = (amount / from_rate) * to_rate
        
        return f"💱 Currency Conversion:\n\n{amount} {from_currency} = {result:.2f} {to_currency}"
    except Exception as e:
        return f"❌ Conversion failed: {str(e)}"

@tool
def date_diff(date1: str, date2: str, unit: str = "days") -> str:
    """Calculate the difference between two dates."""
    try:
        from langchain_office_assistant.utils.helpers import parse_date
        
        d1 = parse_date(date1)
        d2 = parse_date(date2)
        
        diff = abs((d2 - d1).days)
        
        units = {
            "days": diff,
            "weeks": diff / 7,
            "months": diff / 30.44,
            "years": diff / 365.25,
        }
        
        if unit not in units:
            return f"❌ Invalid unit. Supported: days, weeks, months, years"
        
        result = units[unit]
        
        return f"📅 Date Difference:\n\n{date1} ↔ {date2} = {result:.2f} {unit}"
    except Exception as e:
        return f"❌ Date calculation failed: {str(e)}"

@tool
def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between different units."""
    try:
        conversions = {
            "length": {
                "m": 1.0, "km": 0.001, "cm": 100.0, "mm": 1000.0,
                "in": 39.3701, "ft": 3.28084, "yd": 1.09361, "mi": 0.000621371
            },
            "weight": {
                "kg": 1.0, "g": 1000.0, "mg": 1000000.0,
                "lb": 2.20462, "oz": 35.274
            },
            "volume": {
                "l": 1.0, "ml": 1000.0, "gal": 0.264172, "qt": 1.05669
            }
        }
        
        unit_categories = {
            "m": "length", "km": "length", "cm": "length", "mm": "length",
            "in": "length", "ft": "length", "yd": "length", "mi": "length",
            "kg": "weight", "g": "weight", "mg": "weight", "lb": "weight", "oz": "weight",
            "l": "volume", "ml": "volume", "gal": "volume", "qt": "volume"
        }
        
        from_cat = unit_categories.get(from_unit.lower())
        to_cat = unit_categories.get(to_unit.lower())
        
        if not from_cat or not to_cat:
            return f"❌ Unsupported unit. Supported: length (m, km, cm, mm, in, ft, yd, mi), weight (kg, g, mg, lb, oz), volume (l, ml, gal, qt)"
        
        if from_cat != to_cat:
            return f"❌ Units must be in the same category"
        
        from_factor = conversions[from_cat][from_unit.lower()]
        to_factor = conversions[from_cat][to_unit.lower()]
        
        result = (value / from_factor) * to_factor
        
        return f"📏 Unit Conversion:\n\n{value} {from_unit} = {result:.4f} {to_unit}"
    except Exception as e:
        return f"❌ Conversion failed: {str(e)}"

- [ ] **Step 3: Commit**

```bash
git add plugins/calc/
git commit -m "feat: add calc plugin"
```

---

### Task 12: 智能体核心模块

**Files:**
- Create: `langchain_office_assistant/agents/__init__.py`
- Create: `langchain_office_assistant/agents/core.py`
- Create: `langchain_office_assistant/agents/intent_recognizer.py`
- Create: `langchain_office_assistant/agents/memory_manager.py`
- Create: `langchain_office_assistant/agents/trace_recorder.py`

- [ ] **Step 1: Create agents/__init__.py**

```python
from langchain_office_assistant.agents.core import OfficeAgent, create_office_agent, run_office_assistant
from langchain_office_assistant.agents.intent_recognizer import IntentRecognizer
from langchain_office_assistant.agents.memory_manager import MemoryManager
from langchain_office_assistant.agents.trace_recorder import TraceRecorder
from langchain_office_assistant.agents import SYSTEM_PROMPT

__all__ = [
    "OfficeAgent",
    "create_office_agent",
    "run_office_assistant",
    "IntentRecognizer",
    "MemoryManager",
    "TraceRecorder",
    "SYSTEM_PROMPT",
]
```

- [ ] **Step 2: Create agents/core.py**

```python
from typing import List, Dict, Any, Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.plugins import (
    EmailPlugin,
    CalendarPlugin,
    TaskPlugin,
    DocumentPlugin,
    PPTPlugin,
    KnowledgePlugin,
    ChartPlugin,
    CalcPlugin,
)
from langchain_office_assistant.agents.intent_recognizer import IntentRecognizer
from langchain_office_assistant.agents.memory_manager import MemoryManager
from langchain_office_assistant.agents.trace_recorder import TraceRecorder
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a professional office assistant helping users with:

📧 Email Management - Send, search, and manage emails
📅 Calendar & Scheduling - Check schedules and schedule meetings  
✅ Task Management - Create and track tasks and todos
📄 Document Handling - Search and summarize documents
📊 PPT Generation - Create presentations and charts
🧠 Knowledge Base - Search and query knowledge
📈 Chart & Reporting - Generate charts and reports
🔢 Calculations - Perform calculations and conversions

Guidelines:
- Always use the available tools to complete tasks
- Ask for clarification when user requests are ambiguous
- Provide clear, structured responses
- Confirm important actions before executing them
- Be proactive in identifying automation opportunities

Available tools:
- Email: send_email, search_emails, read_email
- Calendar: check_calendar, schedule_meeting
- Task: create_task, list_tasks, update_task
- Document: search_documents, summarize_document, read_document, write_document
- PPT: create_ppt, add_slide, add_chart_to_ppt, save_ppt
- Knowledge: add_document, search_knowledge, query_knowledge, list_documents
- Chart: create_bar_chart, create_line_chart, create_pie_chart, create_radar_chart, create_scatter_plot
- Calc: calculate, statistics, currency_convert, date_diff, unit_convert

Remember to use tools effectively and provide helpful, actionable responses."""

class OfficeAgent:
    def __init__(self, plugins: Optional[List[BasePlugin]] = None, config: Optional[Dict] = None):
        self.config = config or {}
        self.plugins = plugins or self._load_default_plugins()
        
        self.intent_recognizer = IntentRecognizer()
        self.memory_manager = MemoryManager()
        self.trace_recorder = TraceRecorder()
        
        self.model = self._init_model()
        
        for plugin in self.plugins:
            plugin.initialize(config)
            logger.info(f"Loaded plugin: {plugin.name}")
    
    def _load_default_plugins(self) -> List[BasePlugin]:
        return [
            EmailPlugin(),
            CalendarPlugin(),
            TaskPlugin(),
            DocumentPlugin(),
            PPTPlugin(),
            KnowledgePlugin(),
            ChartPlugin(),
            CalcPlugin(),
        ]
    
    def _init_model(self) -> BaseChatModel:
        model_name = self.config.get("agent_model", "gpt-4")
        
        if model_name.startswith("ollama:"):
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model_name[len("ollama:"):], temperature=0.7)
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, temperature=0.7)
    
    def get_all_tools(self) -> List:
        all_tools = []
        for plugin in self.plugins:
            all_tools.extend(plugin.get_tools())
        return all_tools
    
    async def chat(self, message: str, session_id: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        session_id = session_id or self.memory_manager.generate_session_id()
        
        self.trace_recorder.start_trace(session_id)
        self.trace_recorder.record_input(session_id, message)
        
        try:
            memory = self.memory_manager.get_memory(session_id)
            history = [HumanMessage(content=msg["content"]) for msg in memory]
            
            intent = self.intent_recognizer.recognize(message)
            self.trace_recorder.record_intent(session_id, intent)
            
            response = await self._process_message(message, history, intent, session_id)
            
            self.memory_manager.add_memory(session_id, {
                "role": "user",
                "content": message
            })
            self.memory_manager.add_memory(session_id, {
                "role": "assistant",
                "content": response
            })
            
            self.trace_recorder.record_output(session_id, response)
            
            return {
                "response": response,
                "session_id": session_id,
                "intent": intent,
                "trace_id": session_id
            }
        except Exception as e:
            self.trace_recorder.record_error(session_id, str(e))
            logger.error(f"Chat error: {e}")
            return {
                "response": f"❌ Error: {str(e)}",
                "session_id": session_id,
                "error": str(e)
            }
    
    async def _process_message(self, message: str, history: List, intent: Dict, session_id: str) -> str:
        from langchain.tools.render import render_text_description
        from langchain.agents import create_react_agent, AgentExecutor
        
        tools = self.get_all_tools()
        tools_str = render_text_description(tools)
        
        prompt = f"{SYSTEM_PROMPT}\n\n{tools_str}\n\n"
        
        agent = create_react_agent(self.model, tools)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        result = await executor.ainvoke({
            "input": message,
            "chat_history": history
        })
        
        self.trace_recorder.record_tool_calls(session_id, executor.agent.agent_state.get("intermediate_steps", []))
        
        return result.get("output", "No response")
    
    def get_trace(self, session_id: str) -> Dict:
        return self.trace_recorder.get_trace(session_id)
    
    def clear_memory(self, session_id: str) -> None:
        self.memory_manager.clear_memory(session_id)

def create_office_agent(
    model: Union[str, BaseChatModel] = "gpt-4",
    plugins: Optional[List[BasePlugin]] = None,
    **kwargs
) -> OfficeAgent:
    config = {"agent_model": model if isinstance(model, str) else "custom"}
    config.update(kwargs)
    
    return OfficeAgent(plugins=plugins, config=config)

async def run_office_assistant(
    user_input: str,
    model: Union[str, BaseChatModel] = "gpt-4",
    plugins: Optional[List[BasePlugin]] = None,
    stream: bool = False,
) -> str:
    agent = create_office_agent(model=model, plugins=plugins)
    result = await agent.chat(user_input)
    return result["response"]
```

- [ ] **Step 3: Create agents/intent_recognizer.py**

```python
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

class IntentRecognizer:
    def __init__(self):
        self.intent_patterns = {
            "email": ["send email", "send an email", "email to", "email about", "read email", "search email"],
            "calendar": ["schedule meeting", "check calendar", "meeting", "appointment", "schedule"],
            "task": ["create task", "add task", "todo", "task list", "update task", "complete task"],
            "document": ["read document", "write document", "summarize document", "search document"],
            "ppt": ["create ppt", "make presentation", "slide", "powerpoint"],
            "knowledge": ["search knowledge", "query knowledge", "add document", "knowledge base"],
            "chart": ["create chart", "make graph", "visualize data", "plot"],
            "calc": ["calculate", "convert", "statistics", "math", "compute"],
        }
        
        self.model = ChatOpenAI(model="gpt-4", temperature=0)
    
    def recognize(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return {
                        "intent": intent,
                        "confidence": 0.9,
                        "pattern": pattern
                    }
        
        return self._classify_with_llm(message)
    
    def _classify_with_llm(self, message: str) -> Dict[str, Any]:
        try:
            prompt = f"""
Classify the user's intent into one of these categories:
- email: sending, reading, searching emails
- calendar: scheduling meetings, checking calendar
- task: creating, updating, listing tasks
- document: reading, writing, summarizing documents
- ppt: creating presentations
- knowledge: searching, querying knowledge base
- chart: creating charts and graphs
- calc: calculations, conversions, statistics
- general: general conversation, greetings

User message: "{message}"

Return ONLY the category name.
"""
            response = self.model.invoke(prompt)
            intent = response.content.strip().lower()
            
            valid_intents = ["email", "calendar", "task", "document", "ppt", "knowledge", "chart", "calc", "general"]
            
            if intent in valid_intents:
                return {
                    "intent": intent,
                    "confidence": 0.8,
                    "method": "llm"
                }
            
            return {
                "intent": "general",
                "confidence": 0.5,
                "method": "fallback"
            }
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}")
            return {
                "intent": "general",
                "confidence": 0.5,
                "method": "fallback"
            }
```

- [ ] **Step 4: Create agents/memory_manager.py**

```python
from typing import List, Dict, Any, Optional
import redis
import json
from langchain_office_assistant.utils.config import config
from langchain_office_assistant.utils.logger import get_logger
import uuid

logger = get_logger(__name__)

class MemoryManager:
    def __init__(self):
        self.max_history = 20
        try:
            self.redis_client = redis.from_url(config.redis_url)
            self.use_redis = True
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory storage: {e}")
            self.use_redis = False
            self.memory_store: Dict[str, List] = {}
    
    def generate_session_id(self) -> str:
        return str(uuid.uuid4())
    
    def get_memory(self, session_id: str) -> List[Dict]:
        if self.use_redis:
            try:
                data = self.redis_client.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
                return []
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return []
        else:
            return self.memory_store.get(session_id, [])
    
    def add_memory(self, session_id: str, message: Dict) -> None:
        memory = self.get_memory(session_id)
        memory.append(message)
        
        if len(memory) > self.max_history:
            memory = memory[-self.max_history:]
        
        if self.use_redis:
            try:
                self.redis_client.set(f"session:{session_id}", json.dumps(memory), ex=3600*24)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        else:
            self.memory_store[session_id] = memory
    
    def clear_memory(self, session_id: str) -> None:
        if self.use_redis:
            try:
                self.redis_client.delete(f"session:{session_id}")
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        else:
            if session_id in self.memory_store:
                del self.memory_store[session_id]
    
    def get_session_list(self) -> List[str]:
        if self.use_redis:
            try:
                keys = self.redis_client.keys("session:*")
                return [k.decode("utf-8").replace("session:", "") for k in keys]
            except Exception as e:
                logger.error(f"Redis keys error: {e}")
                return []
        else:
            return list(self.memory_store.keys())
```

- [ ] **Step 5: Create agents/trace_recorder.py**

```python
from typing import Dict, Any, List, Optional
import json
import time
from langchain_office_assistant.utils.logger import get_logger
import uuid

logger = get_logger(__name__)

class TraceRecorder:
    def __init__(self):
        self.traces: Dict[str, Dict] = {}
    
    def start_trace(self, session_id: str) -> None:
        self.traces[session_id] = {
            "trace_id": str(uuid.uuid4()),
            "session_id": session_id,
            "start_time": time.time(),
            "end_time": None,
            "input": None,
            "output": None,
            "intent": None,
            "tool_calls": [],
            "errors": [],
            "steps": []
        }
    
    def record_input(self, session_id: str, input_text: str) -> None:
        if session_id in self.traces:
            self.traces[session_id]["input"] = input_text
            self._add_step(session_id, "input_received", {"text": input_text})
    
    def record_output(self, session_id: str, output_text: str) -> None:
        if session_id in self.traces:
            self.traces[session_id]["output"] = output_text
            self.traces[session_id]["end_time"] = time.time()
            self._add_step(session_id, "output_generated", {"text": output_text})
    
    def record_intent(self, session_id: str, intent: Dict) -> None:
        if session_id in self.traces:
            self.traces[session_id]["intent"] = intent
            self._add_step(session_id, "intent_recognized", intent)
    
    def record_tool_call(self, session_id: str, tool_name: str, args: Dict, result: Any) -> None:
        if session_id in self.traces:
            tool_call = {
                "tool_name": tool_name,
                "args": args,
                "result": result,
                "timestamp": time.time()
            }
            self.traces[session_id]["tool_calls"].append(tool_call)
            self._add_step(session_id, "tool_called", tool_call)
    
    def record_tool_calls(self, session_id: str, tool_calls: List) -> None:
        if session_id in self.traces:
            for call in tool_calls:
                if hasattr(call, 'tool_call'):
                    tool_name = call.tool_call.tool_name
                    args = call.tool_call.tool_args
                    result = call.observation
                    self.record_tool_call(session_id, tool_name, args, result)
    
    def record_error(self, session_id: str, error: str) -> None:
        if session_id in self.traces:
            self.traces[session_id]["errors"].append({
                "error": error,
                "timestamp": time.time()
            })
            self._add_step(session_id, "error", {"message": error})
    
    def _add_step(self, session_id: str, step_type: str, details: Dict) -> None:
        if session_id in self.traces:
            self.traces[session_id]["steps"].append({
                "type": step_type,
                "details": details,
                "timestamp": time.time()
            })
    
    def get_trace(self, session_id: str) -> Optional[Dict]:
        return self.traces.get(session_id)
    
    def get_trace_summary(self, session_id: str) -> Optional[Dict]:
        trace = self.traces.get(session_id)
        if not trace:
            return None
        
        return {
            "trace_id": trace["trace_id"],
            "session_id": trace["session_id"],
            "duration": trace["end_time"] - trace["start_time"] if trace["end_time"] else None,
            "input": trace["input"],
            "output": trace["output"],
            "intent": trace["intent"],
            "tool_count": len(trace["tool_calls"]),
            "error_count": len(trace["errors"])
        }
    
    def list_traces(self) -> List[Dict]:
        summaries = []
        for session_id, trace in self.traces.items():
            summaries.append(self.get_trace_summary(session_id))
        return sorted(summaries, key=lambda x: x["trace_id"], reverse=True)
    
    def export_trace(self, session_id: str) -> str:
        trace = self.traces.get(session_id)
        if not trace:
            return "Trace not found"
        return json.dumps(trace, indent=2, ensure_ascii=False)
```

- [ ] **Step 6: Commit**

```bash
git add agents/
git commit -m "feat: add agent core modules"
```

---

### Task 13: API服务模块

**Files:**
- Create: `langchain_office_assistant/api/__init__.py`
- Create: `langchain_office_assistant/api/main.py`
- Create: `langchain_office_assistant/api/endpoints/__init__.py`
- Create: `langchain_office_assistant/api/endpoints/chat.py`
- Create: `langchain_office_assistant/api/endpoints/trace.py`
- Create: `langchain_office_assistant/api/dependencies.py`

- [ ] **Step 1: Create api/__init__.py**

```python
from langchain_office_assistant.api.main import app
from langchain_office_assistant.api.endpoints.chat import router as chat_router
from langchain_office_assistant.api.endpoints.trace import router as trace_router

__all__ = ["app", "chat_router", "trace_router"]
```

- [ ] **Step 2: Create api/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_office_assistant.api.endpoints.chat import router as chat_router
from langchain_office_assistant.api.endpoints.trace import router as trace_router
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Office Agent API",
    description="API for Office Agent - Your AI-powered office assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(trace_router, prefix="/api", tags=["trace"])

@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "office-agent"}

@app.get("/api/plugins", tags=["plugins"])
async def list_plugins():
    from langchain_office_assistant.plugins import (
        EmailPlugin,
        CalendarPlugin,
        TaskPlugin,
        DocumentPlugin,
        PPTPlugin,
        KnowledgePlugin,
        ChartPlugin,
        CalcPlugin,
    )
    
    plugins = [
        EmailPlugin().get_info(),
        CalendarPlugin().get_info(),
        TaskPlugin().get_info(),
        DocumentPlugin().get_info(),
        PPTPlugin().get_info(),
        KnowledgePlugin().get_info(),
        ChartPlugin().get_info(),
        CalcPlugin().get_info(),
    ]
    
    return {"plugins": plugins}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 3: Create api/endpoints/__init__.py**

```python
from langchain_office_assistant.api.endpoints.chat import router as chat_router
from langchain_office_assistant.api.endpoints.trace import router as trace_router

__all__ = ["chat_router", "trace_router"]
```

- [ ] **Step 4: Create api/endpoints/chat.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from langchain_office_assistant.api.dependencies import get_agent

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: Optional[Dict] = None
    trace_id: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        agent = get_agent()
        result = await agent.chat(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    try:
        agent = get_agent()
        agent.clear_memory(session_id)
        return {"status": "success", "message": "Session cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 5: Create api/endpoints/trace.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from langchain_office_assistant.api.dependencies import get_agent

router = APIRouter()

@router.get("/trace/{session_id}")
async def get_trace(session_id: str):
    try:
        agent = get_agent()
        trace = agent.get_trace(session_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{session_id}/summary")
async def get_trace_summary(session_id: str):
    try:
        agent = get_agent()
        trace = agent.trace_recorder.get_trace_summary(session_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/traces")
async def list_traces():
    try:
        agent = get_agent()
        traces = agent.trace_recorder.list_traces()
        return {"traces": traces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{session_id}/export")
async def export_trace(session_id: str):
    try:
        agent = get_agent()
        export = agent.trace_recorder.export_trace(session_id)
        
        if export == "Trace not found":
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {"trace": export}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 6: Create api/dependencies.py**

```python
from typing import Optional
from langchain_office_assistant.agents import OfficeAgent

_agent: Optional[OfficeAgent] = None

def get_agent() -> OfficeAgent:
    global _agent
    if _agent is None:
        _agent = OfficeAgent()
    return _agent
```

- [ ] **Step 7: Commit**

```bash
git add api/
git commit -m "feat: add API service module"
```

---

### Task 14: CLI模块

**Files:**
- Create: `langchain_office_assistant/cli/__init__.py`
- Create: `langchain_office_assistant/cli/main.py`

- [ ] **Step 1: Create cli/__init__.py**

```python
from langchain_office_assistant.cli.main import main

__all__ = ["main"]
```

- [ ] **Step 2: Create cli/main.py**

```python
import argparse
import asyncio
from typing import Optional
from langchain_office_assistant.agents import create_office_agent
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

async def chat_interactive(model: str = "gpt-4"):
    """Start interactive chat mode."""
    print("🚀 Office Agent - Interactive Mode")
    print("==================================")
    print("Type 'exit' or 'quit' to exit")
    print("Type 'clear' to clear the screen")
    print("Type 'trace' to get current trace")
    print("==================================\n")
    
    agent = create_office_agent(model=model)
    session_id = None
    
    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == "clear":
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            
            if user_input.lower() == "trace":
                if session_id:
                    trace = agent.get_trace(session_id)
                    print(f"\n📋 Trace for session {session_id}:")
                    print(trace)
                else:
                    print("⚠️ No active session")
                continue
            
            result = await agent.chat(user_input, session_id=session_id)
            session_id = result["session_id"]
            
            print(f"\n🤖 Assistant: {result['response']}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

async def chat_single(message: str, model: str = "gpt-4"):
    """Run a single chat message."""
    agent = create_office_agent(model=model)
    result = await agent.chat(message)
    print(result["response"])

def main():
    parser = argparse.ArgumentParser(
        prog="office-agent",
        description="Office Agent - Your AI-powered office assistant"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    chat_parser = subparsers.add_parser("chat", help="Chat with the agent")
    chat_parser.add_argument("-m", "--model", default="gpt-4", help="Model name")
    chat_parser.add_argument("-t", "--text", help="Single text input")
    
    list_parser = subparsers.add_parser("list", help="List available plugins")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.command == "chat":
        if args.text:
            asyncio.run(chat_single(args.text, model=args.model))
        else:
            asyncio.run(chat_interactive(model=args.model))
    
    elif args.command == "list":
        from langchain_office_assistant.plugins import (
            EmailPlugin,
            CalendarPlugin,
            TaskPlugin,
            DocumentPlugin,
            PPTPlugin,
            KnowledgePlugin,
            ChartPlugin,
            CalcPlugin,
        )
        
        plugins = [
            EmailPlugin(),
            CalendarPlugin(),
            TaskPlugin(),
            DocumentPlugin(),
            PPTPlugin(),
            KnowledgePlugin(),
            ChartPlugin(),
            CalcPlugin(),
        ]
        
        print("📦 Available Plugins:")
        print("=====================\n")
        
        for plugin in plugins:
            info = plugin.get_info()
            print(f"🔹 {info['name']}")
            print(f"   Description: {info['description']}")
            print(f"   Version: {info['version']}")
            if args.verbose:
                print(f"   Tools: {', '.join(info['tools'])}")
            print()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add cli/
git commit -m "feat: add CLI module"
```

---

### Task 15: 数据层模块

**Files:**
- Create: `langchain_office_assistant/data/__init__.py`
- Create: `langchain_office_assistant/data/vector_db.py`
- Create: `langchain_office_assistant/data/file_store.py`

- [ ] **Step 1: Create data/__init__.py**

```python
from langchain_office_assistant.data.vector_db import VectorDB
from langchain_office_assistant.data.file_store import FileStore

__all__ = ["VectorDB", "FileStore"]
```

- [ ] **Step 2: Create data/vector_db.py**

```python
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS, Milvus, Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_office_assistant.utils.config import config
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

class VectorDB:
    def __init__(self, db_type: Optional[str] = None):
        self.db_type = db_type or config.vector_db_type
        self.vector_store = None
        self._init_store()
    
    def _init_store(self):
        try:
            embeddings = OpenAIEmbeddings(
                api_key=config.openai_api_key,
                model="text-embedding-3-small"
            )
            
            if self.db_type == "milvus":
                self.vector_store = Milvus(
                    embedding_function=embeddings,
                    connection_args={"host": "localhost", "port": "19530"}
                )
            elif self.db_type == "qdrant":
                self.vector_store = Qdrant.from_documents(
                    [],
                    embeddings,
                    location=":memory:"
                )
            else:
                if config.debug_mode:
                    self.vector_store = FAISS.from_texts(
                        ["Initial document"],
                        embeddings
                    )
                else:
                    if FAISS.exists_local("vector_db"):
                        self.vector_store = FAISS.load_local(
                            "vector_db",
                            embeddings,
                            allow_dangerous_deserialization=True
                        )
                    else:
                        self.vector_store = FAISS.from_texts(
                            ["Initial document"],
                            embeddings
                        )
                        self.vector_store.save_local("vector_db")
            
            logger.info(f"VectorDB initialized with {self.db_type}")
        except Exception as e:
            logger.error(f"Failed to initialize VectorDB: {e}")
    
    def add_documents(self, documents: List[Document], metadatas: Optional[List[Dict]] = None) -> None:
        if self.vector_store:
            self.vector_store.add_documents(documents, metadatas=metadatas)
            if self.db_type == "faiss":
                self.vector_store.save_local("vector_db")
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        if self.vector_store:
            self.vector_store.add_texts(texts, metadatas=metadatas)
            if self.db_type == "faiss":
                self.vector_store.save_local("vector_db")
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        if self.vector_store:
            return self.vector_store.similarity_search(query, k=k)
        return []
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        if self.vector_store:
            return self.vector_store.similarity_search_with_score(query, k=k)
        return []
    
    def delete(self, ids: List[str]) -> None:
        if self.vector_store and hasattr(self.vector_store, 'delete'):
            self.vector_store.delete(ids)
    
    def clear(self) -> None:
        if self.vector_store:
            self.vector_store = None
            self._init_store()
```

- [ ] **Step 3: Create data/file_store.py**

```python
from typing import Dict, Any, Optional
import os
import shutil
from datetime import datetime
from langchain_office_assistant.utils.logger import get_logger

logger = get_logger(__name__)

class FileStore:
    def __init__(self, base_path: str = "uploads"):
        self.base_path = base_path
        self._init_storage()
    
    def _init_storage(self):
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            logger.info(f"Created storage directory: {self.base_path}")
    
    def save_file(self, file_content: bytes, filename: str, folder: str = "documents") -> str:
        folder_path = os.path.join(self.base_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        filepath = os.path.join(folder_path, filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"File saved: {filepath}")
        return filepath
    
    def read_file(self, filepath: str) -> Optional[bytes]:
        full_path = os.path.join(self.base_path, filepath) if not filepath.startswith(self.base_path) else filepath
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                return f.read()
        return None
    
    def delete_file(self, filepath: str) -> bool:
        full_path = os.path.join(self.base_path, filepath) if not filepath.startswith(self.base_path) else filepath
        
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"File deleted: {full_path}")
            return True
        return False
    
    def list_files(self, folder: str = "documents") -> list:
        folder_path = os.path.join(self.base_path, folder)
        
        if not os.path.exists(folder_path):
            return []
        
        files = []
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                files.append({
                    "name": filename,
                    "path": filepath,
                    "size": os.path.getsize(filepath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
        
        return files
    
    def get_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        full_path = os.path.join(self.base_path, filepath) if not filepath.startswith(self.base_path) else filepath
        
        if os.path.exists(full_path):
            return {
                "name": os.path.basename(full_path),
                "path": full_path,
                "size": os.path.getsize(full_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
            }
        return None
    
    def create_folder(self, folder_name: str, parent_folder: str = "documents") -> bool:
        folder_path = os.path.join(self.base_path, parent_folder, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            logger.info(f"Folder created: {folder_path}")
            return True
        return False
    
    def delete_folder(self, folder_name: str, parent_folder: str = "documents") -> bool:
        folder_path = os.path.join(self.base_path, parent_folder, folder_name)
        
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logger.info(f"Folder deleted: {folder_path}")
            return True
        return False
```

- [ ] **Step 4: Commit**

```bash
git add data/
git commit -m "feat: add data layer modules"
```

---

### Task 16: 测试模块

**Files:**
- Create: `langchain_office_assistant/tests/__init__.py`
- Create: `langchain_office_assistant/tests/test_agents.py`
- Create: `langchain_office_assistant/tests/test_plugins.py`

- [ ] **Step 1: Create tests/__init__.py**

```python
__all__ = []
```

- [ ] **Step 2: Create tests/test_agents.py**

```python
import pytest
import asyncio
from langchain_office_assistant.agents import create_office_agent
from langchain_office_assistant.agents.intent_recognizer import IntentRecognizer
from langchain_office_assistant.agents.memory_manager import MemoryManager

class TestIntentRecognizer:
    def test_recognize_email_intent(self):
        recognizer = IntentRecognizer()
        intent = recognizer.recognize("Send an email to John")
        assert intent["intent"] == "email"
    
    def test_recognize_calendar_intent(self):
        recognizer = IntentRecognizer()
        intent = recognizer.recognize("Schedule a meeting tomorrow")
        assert intent["intent"] == "calendar"
    
    def test_recognize_task_intent(self):
        recognizer = IntentRecognizer()
        intent = recognizer.recognize("Create a task to finish the report")
        assert intent["intent"] == "task"

class TestMemoryManager:
    def test_memory_storage(self):
        manager = MemoryManager()
        session_id = manager.generate_session_id()
        
        manager.add_memory(session_id, {"role": "user", "content": "Hello"})
        memory = manager.get_memory(session_id)
        
        assert len(memory) == 1
        assert memory[0]["content"] == "Hello"
    
    def test_memory_limits(self):
        manager = MemoryManager()
        session_id = manager.generate_session_id()
        
        for i in range(25):
            manager.add_memory(session_id, {"role": "user", "content": f"Message {i}"})
        
        memory = manager.get_memory(session_id)
        assert len(memory) == 20

class TestOfficeAgent:
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        agent = create_office_agent(model="gpt-4")
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_agent_chat(self):
        agent = create_office_agent(model="gpt-4")
        result = await agent.chat("Hello")
        assert "response" in result
        assert "session_id" in result
```

- [ ] **Step 3: Create tests/test_plugins.py**

```python
import pytest
from langchain_office_assistant.plugins.email import EmailPlugin
from langchain_office_assistant.plugins.calendar import CalendarPlugin
from langchain_office_assistant.plugins.task import TaskPlugin
from langchain_office_assistant.plugins.document import DocumentPlugin
from langchain_office_assistant.plugins.calc import CalcPlugin

class TestEmailPlugin:
    def test_send_email(self):
        plugin = EmailPlugin()
        result = plugin.execute("send_email", to=["test@example.com"], subject="Test", body="Hello")
        assert "Email sent successfully" in result
    
    def test_search_emails(self):
        plugin = EmailPlugin()
        result = plugin.execute("search_emails", keyword="会议")
        assert "Found" in result

class TestCalendarPlugin:
    def test_check_calendar(self):
        plugin = CalendarPlugin()
        result = plugin.execute("check_calendar", date="2025-01-15")
        assert "Meetings" in result
    
    def test_schedule_meeting(self):
        plugin = CalendarPlugin()
        result = plugin.execute(
            "schedule_meeting",
            title="Test Meeting",
            date="2025-01-20",
            time="10:00",
            duration_minutes=60,
            participants=["test@example.com"]
        )
        assert "Meeting scheduled successfully" in result

class TestTaskPlugin:
    def test_create_task(self):
        plugin = TaskPlugin()
        result = plugin.execute("create_task", title="Test Task")
        assert "Task created successfully" in result
    
    def test_list_tasks(self):
        plugin = TaskPlugin()
        result = plugin.execute("list_tasks")
        assert "Tasks" in result

class TestCalcPlugin:
    def test_calculate(self):
        plugin = CalcPlugin()
        result = plugin.execute("calculate", expression="2 + 2")
        assert "4" in result
    
    def test_statistics(self):
        plugin = CalcPlugin()
        result = plugin.execute("statistics", numbers=[1, 2, 3, 4, 5])
        assert "mean" in result.lower()
```

- [ ] **Step 4: Run tests**

```bash
cd /workspace/langchain_office_assistant
pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "feat: add test modules"
```

---

### Task 17: Docker配置

**Files:**
- Create: `langchain_office_assistant/docker/Dockerfile`
- Create: `langchain_office_assistant/docker/docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create docker/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "langchain_office_assistant.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker/docker-compose.yml**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AGENT_MODEL=gpt-4
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - redis
    volumes:
      - .:/app
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

- [ ] **Step 3: Create .env.example**

```env
# Agent Configuration
AGENT_MODEL=gpt-4
OPENAI_API_KEY=your-api-key-here
OLLAMA_BASE_URL=http://localhost:11434

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Vector Database Configuration
VECTOR_DB_URL=http://localhost:19530
VECTOR_DB_TYPE=faiss

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=false

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

- [ ] **Step 4: Commit**

```bash
git add docker/ .env.example
git commit -m "feat: add Docker configuration"
```

---

### Task 18: 更新根目录文件

**Files:**
- Update: `langchain_office_assistant/__init__.py`
- Create: `langchain_office_assistant/README.md`

- [ ] **Step 1: Update root __init__.py**

```python
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
```

- [ ] **Step 2: Create README.md**

```markdown
# Office Agent - 办公智能体

基于 LangChain + LangGraph 构建的插件化办公智能体系统，提供全面的办公自动化能力。

## 功能特性

- 📧 **邮件管理** - 发送、搜索、阅读邮件
- 📅 **日历管理** - 查询日程、创建会议
- ✅ **任务管理** - 创建、列表、状态更新
- 📄 **文档处理** - Word/Excel/PDF读写
- 📊 **PPT生成** - 模板支持、图表嵌入
- 🧠 **知识库** - 向量检索、多模态支持
- 📈 **图表报告** - 折线图、柱状图、雷达图等
- 🔢 **计算工具** - 公式计算、数据统计
- 🤖 **意图识别** - 上下文理解、多轮对话
- 📝 **计算追溯** - 完整思考过程记录

## 技术栈

- **框架**: LangChain + LangGraph
- **API框架**: FastAPI
- **文档处理**: python-docx, openpyxl, PyPDF2
- **PPT生成**: python-pptx
- **图表生成**: matplotlib, plotly
- **向量数据库**: FAISS/Milvus/Qdrant
- **部署**: Docker, Docker Compose

## 快速开始

### 安装

```bash
pip install langchain-office-assistant
```

### 使用示例

```python
from langchain_office_assistant.agents import create_office_agent

agent = create_office_agent(model="gpt-4")
result = await agent.chat("帮我安排明天下午3点的会议")
print(result["response"])
```

### CLI使用

```bash
# 交互式聊天
office-agent chat

# 单条消息
office-agent chat -t "帮我创建一个任务"

# 列出可用插件
office-agent list -v
```

### API使用

```bash
# 启动API服务
uvicorn langchain_office_assistant.api.main:app --host 0.0.0.0 --port 8000

# 调用API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我发送一封邮件"}'
```

## 项目结构

```
langchain_office_assistant/
├── agents/           # 智能体核心
├── plugins/          # 插件系统
├── tools/            # 工具封装
├── utils/            # 工具函数
├── data/             # 数据层
├── api/              # API服务
├── cli/              # 命令行接口
├── docker/           # Docker配置
└── tests/            # 测试用例
```

## 配置

创建 `.env` 文件：

```env
AGENT_MODEL=gpt-4
OPENAI_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
```

## 开发

```bash
# 安装依赖
pip install -e .

# 运行测试
pytest tests/ -v

# 启动开发服务器
uvicorn langchain_office_assistant.api.main:app --reload
```

## 许可证

MIT License
```

- [ ] **Step 3: Commit**

```bash
git add __init__.py README.md
git commit -m "feat: update root files and README"
```

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-11-office-agent-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**