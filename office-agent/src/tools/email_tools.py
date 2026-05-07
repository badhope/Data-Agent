"""
Office Agent Tools - Email Module
邮件管理工具集
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field


# ==================== Tool Input Schemas ====================

class SendEmailInput(BaseModel):
    """发送邮件输入参数"""
    to: List[str] = Field(description="收件人邮箱地址列表")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件正文内容")
    cc: Optional[List[str]] = Field(default=None, description="抄送人邮箱地址列表")
    bcc: Optional[List[str]] = Field(default=None, description="密送人邮箱地址列表")


class SearchEmailInput(BaseModel):
    """搜索邮件输入参数"""
    keyword: str = Field(description="搜索关键词")
    folder: str = Field(default="inbox", description="邮件文件夹: inbox, sent, draft, spam")
    sender: Optional[str] = Field(default=None, description="发件人邮箱")
    date_from: Optional[str] = Field(default=None, description="开始日期 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(default=None, description="结束日期 (YYYY-MM-DD)")
    max_results: int = Field(default=10, description="最大返回数量")


class ReadEmailInput(BaseModel):
    """读取邮件输入参数"""
    email_id: str = Field(description="邮件 ID 或序号")
    folder: str = Field(default="inbox", description="邮件文件夹")


class ReplyEmailInput(BaseModel):
    """回复邮件输入参数"""
    email_id: str = Field(description="要回复的邮件 ID")
    body: str = Field(description="回复内容")
    reply_all: bool = Field(default=False, description="是否回复全部")


# ==================== Mock Email Data Store ====================

class MockEmailStore:
    """模拟邮件数据存储（实际项目中应连接真实邮件服务）"""
    
    def __init__(self):
        self.emails = [
            {
                "id": "email_001",
                "folder": "inbox",
                "from": "zhangsan@company.com",
                "to": ["assistant@company.com"],
                "cc": [],
                "subject": "项目进度汇报",
                "body": "张总，\n\n本周项目进度如下：\n1. 前端开发完成 80%\n2. 后端 API 联调中\n3. 预计下周一完成测试\n\n请查收。",
                "date": "2025-01-14 10:30",
                "read": True
            },
            {
                "id": "email_002",
                "folder": "inbox",
                "from": "lisi@company.com",
                "to": ["assistant@company.com"],
                "cc": ["wangwu@company.com"],
                "subject": "周五会议通知",
                "body": "各位同事，\n\n本周五下午3点有产品评审会议，请准时参加。\n地点：3号会议室\n议题：Q1产品规划",
                "date": "2025-01-13 14:20",
                "read": False
            },
            {
                "id": "email_003",
                "folder": "inbox",
                "from": "hr@company.com",
                "to": ["all@company.com"],
                "cc": [],
                "subject": "年会通知",
                "body": "全体员工：\n\n公司年会将于1月20日举行，请各部门提前安排好工作。",
                "date": "2025-01-12 09:00",
                "read": True
            }
        ]
    
    def get_email(self, email_id: str, folder: str = "inbox") -> Optional[Dict]:
        for email in self.emails:
            if email["id"] == email_id and email["folder"] == folder:
                return email
        return None
    
    def search(self, keyword: str, folder: str = "inbox", 
               sender: Optional[str] = None, max_results: int = 10) -> List[Dict]:
        results = []
        for email in self.emails:
            if email["folder"] != folder:
                continue
            if keyword.lower() in email["subject"].lower() or keyword.lower() in email["body"].lower():
                if sender is None or email["from"] == sender:
                    results.append(email)
                    if len(results) >= max_results:
                        break
        return results
    
    def send(self, to: List[str], subject: str, body: str, 
             cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> Dict:
        new_email = {
            "id": f"email_{len(self.emails) + 1:03d}",
            "folder": "sent",
            "from": "assistant@company.com",
            "to": to,
            "cc": cc or [],
            "bcc": bcc or [],
            "subject": subject,
            "body": body,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "read": True
        }
        self.emails.append(new_email)
        return new_email


# 全局邮件存储实例
_email_store = MockEmailStore()


# ==================== Email Tools ====================

@tool(args_schema=SendEmailInput, return_direct=True)
def send_email(
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> str:
    """
    发送邮件给指定收件人。
    
    当用户要求发送邮件、通知某人、或者需要与他人沟通时使用此工具。
    
    Args:
        to: 收件人邮箱列表
        subject: 邮件主题，应简洁明了
        body: 邮件正文内容
        cc: 抄送人列表（可选）
        bcc: 密送人列表（可选）
    
    Returns:
        发送结果，包含邮件ID和发送状态
    """
    try:
        # 实际项目中这里应该调用邮件服务的 API
        # 例如：Microsoft Graph API, Gmail API, 或企业自建邮件系统
        
        email = _email_store.send(to, subject, body, cc, bcc)
        
        recipients = ", ".join(to)
        cc_str = f", 抄送: {', '.join(cc)}" if cc else ""
        
        result = f"""✅ 邮件发送成功！

📧 邮件信息：
   - 收件人: {recipients}{cc_str}
   - 主题: {subject}
   - 时间: {email['date']}
   - 邮件ID: {email['id']}

📝 邮件内容预览：
{body[:100]}{'...' if len(body) > 100 else ''}"""
        
        return result
        
    except Exception as e:
        return f"❌ 邮件发送失败: {str(e)}"


@tool(args_schema=SearchEmailInput, return_direct=False)
def search_emails(
    keyword: str,
    folder: str = "inbox",
    sender: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    搜索邮件。
    
    当用户要查找邮件、回顾历史通信、或者找特定信息时使用此工具。
    
    Args:
        keyword: 搜索关键词，可以是主题、内容中的词
        folder: 邮件文件夹，默认收件箱
        sender: 指定发件人（可选）
        date_from: 开始日期（可选，格式: YYYY-MM-DD）
        date_to: 结束日期（可选，格式: YYYY-MM-DD）
        max_results: 最大返回数量，默认10封
    
    Returns:
        搜索结果列表
    """
    try:
        results = _email_store.search(keyword, folder, sender, max_results)
        
        if not results:
            return f"🔍 没有找到包含「{keyword}」的邮件"
        
        output = f"🔍 找到 {len(results)} 封相关邮件：\n\n"
        
        for i, email in enumerate(results, 1):
            read_status = "✓" if email["read"] else "○"
            output += f"""【{i}】{read_status} {email['subject']}
   发件人: {email['from']}
   时间: {email['date']}
   预览: {email['body'][:80]}...
   
"""
        
        return output.strip()
        
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


@tool(args_schema=ReadEmailInput, return_direct=False)
def read_email(email_id: str, folder: str = "inbox") -> str:
    """
    读取指定邮件的完整内容。
    
    当用户想查看某封邮件的详细内容时使用此工具。
    
    Args:
        email_id: 邮件ID或序号
        folder: 邮件文件夹
    
    Returns:
        邮件完整内容
    """
    try:
        email = _email_store.get_email(email_id, folder)
        
        if not email:
            return f"❌ 未找到邮件: {email_id}"
        
        # 标记为已读
        email["read"] = True
        
        cc_str = f"\n📑 抄送: {', '.join(email['cc'])}" if email['cc'] else ""
        
        result = f"""📧 邮件详情

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 主题: {email['subject']}
👤 发件人: {email['from']}
📅 时间: {email['date']}
📩 收件人: {', '.join(email['to'])}{cc_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{email['body']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
邮件ID: {email['id']} | 文件夹: {email['folder']}
"""        
        return result
        
    except Exception as e:
        return f"❌ 读取邮件失败: {str(e)}"


@tool(args_schema=ReplyEmailInput, return_direct=True)
def reply_email(email_id: str, body: str, reply_all: bool = False) -> str:
    """
    回复邮件。
    
    当用户要回复某封收到的邮件时使用此工具。
    
    Args:
        email_id: 要回复的邮件ID
        body: 回复内容
        reply_all: 是否回复全部（包含抄送人）
    
    Returns:
        回复结果
    """
    try:
        # 获取原邮件
        original = None
        for email in _email_store.emails:
            if email["id"] == email_id:
                original = email
                break
        
        if not original:
            return f"❌ 未找到邮件: {email_id}"
        
        # 构建回复邮件
        subject = f"Re: {original['subject']}" if not original['subject'].startswith("Re:") else original['subject']
        
        # 回复收件人
        to = [original['from']]
        
        # 如果 reply_all，包含抄送人
        if reply_all and original['cc']:
            to.extend(original['cc'])
        
        # 发送回复
        reply_body = f"""您好，

{body}



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
原文来自: {original['from']}
原文时间: {original['date']}
原文内容:
{original['body']}"""
        
        result = send_email.invoke({
            "to": to,
            "subject": subject,
            "body": reply_body
        })
        
        return result
        
    except Exception as e:
        return f"❌ 回复邮件失败: {str(e)}"


@tool(return_direct=False)
def list_email_folders() -> str:
    """
    列出所有邮件文件夹。
    
    当用户想了解邮件账户的文件夹结构时使用此工具。
    
    Returns:
        文件夹列表
    """
    folders = {
        "inbox": {"count": 3, "unread": 1, "description": "收件箱"},
        "sent": {"count": 0, "unread": 0, "description": "已发送"},
        "draft": {"count": 0, "unread": 0, "description": "草稿箱"},
        "spam": {"count": 5, "unread": 5, "description": "垃圾邮件"},
        "trash": {"count": 10, "unread": 0, "description": "回收站"}
    }
    
    output = "📁 邮件文件夹：\n\n"
    
    for folder, info in folders.items():
        unread_str = f" ({info['unread']}封未读)" if info['unread'] > 0 else ""
        output += f"  📂 {folder}: {info['count']}封{unread_str} - {info['description']}\n"
    
    return output


# ==================== Tool Exports ====================

EMAIL_TOOLS = [
    send_email,
    search_emails,
    read_email,
    reply_email,
    list_email_folders
]

__all__ = [
    "send_email",
    "search_emails", 
    "read_email",
    "reply_email",
    "list_email_folders",
    "EMAIL_TOOLS"
]
