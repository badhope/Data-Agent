"""Email tools module."""

from langchain_core.tools import tool
from typing import List
from datetime import datetime


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

    def get_email(self, email_id: str) -> dict:
        for email in self.emails:
            if email["id"] == email_id:
                return email
        return None


_email_store = MockEmailStore()


@tool
def send_email(to: List[str], subject: str, body: str) -> str:
    """Send an email to specified recipients."""
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
    """Search emails by keyword."""
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
    """Read a specific email by ID."""
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
