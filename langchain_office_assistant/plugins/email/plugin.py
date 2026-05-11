from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
from langchain_office_assistant.utils.helpers import validate_email
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