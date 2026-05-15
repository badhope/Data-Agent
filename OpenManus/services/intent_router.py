"""
意图识别路由 - 将用户对话消息路由到对应的功能API
对标豆包/ChatGPT的对话内功能调用体验
"""
import re
import json
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


# 意图匹配规则
INTENT_RULES = [
    {
        "name": "polish",
        "keywords": ["润色", "修改", "优化文本", "改写", "学术规范", "polish", "refine"],
        "patterns": [
            r"润色.{0,10}(文本|内容|这段|以下)",
            r"(请|帮我).{0,5}润色",
            r"(文本|内容).{0,5}(更|更加).{0,5}(学术|正式|专业|简洁)",
        ],
        "priority": 10,
    },
    {
        "name": "ppt",
        "keywords": ["ppt", "PPT", "幻灯片", "演示文稿", "slides", "presentation"],
        "patterns": [
            r"生成.{0,5}(PPT|ppt|幻灯片|演示文稿)",
            r"(帮我|请).{0,5}(做|制作|生成).{0,5}PPT",
            r"PPT.{0,5}(主题|关于|内容)",
        ],
        "priority": 10,
    },
    {
        "name": "todo",
        "keywords": ["待办", "todo", "TODO", "行动项", "任务提取", "事项"],
        "patterns": [
            r"提取.{0,5}(待办|行动项|任务|todo)",
            r"(帮我|请).{0,5}(提取|整理).{0,5}(待办|行动项)",
            r"(文本|内容).{0,5}(待办|行动项)",
        ],
        "priority": 8,
    },
    {
        "name": "meeting",
        "keywords": ["会议纪要", "会议记录", "会议总结", "meeting", "minutes"],
        "patterns": [
            r"生成.{0,5}(会议纪要|会议记录|会议总结)",
            r"(帮我|请).{0,5}(整理|生成|总结).{0,5}会议",
            r"会议.{0,5}(纪要|记录|总结)",
        ],
        "priority": 8,
    },
    {
        "name": "weekly_report",
        "keywords": ["周报", "日报", "月报", "工作汇报", "工作报告"],
        "patterns": [
            r"生成.{0,5}(周报|日报|月报|工作汇报)",
            r"(帮我|请).{0,5}(写|生成|整理).{0,5}(周报|日报|月报)",
            r"(本周|今天|这个月).{0,5}(工作|完成|做了)",
        ],
        "priority": 7,
    },
    {
        "name": "summary",
        "keywords": ["摘要", "总结", "概括", "提炼", "summarize", "summary"],
        "patterns": [
            r"(帮我|请).{0,5}(总结|摘要|概括|提炼)",
            r"(文献|论文|文章).{0,5}(摘要|总结|概括)",
            r"核心.{0,5}(观点|内容|思想)",
        ],
        "priority": 6,
    },
]


def detect_intent(message: str) -> Optional[str]:
    """检测用户消息的意图"""
    if not message or len(message) < 2:
        return None

    message_lower = message.lower()

    best_intent = None
    best_score = 0

    for rule in INTENT_RULES:
        score = 0

        # 关键词匹配
        for kw in rule["keywords"]:
            if kw.lower() in message_lower:
                score += rule["priority"]

        # 正则模式匹配
        for pattern in rule["patterns"]:
            if re.search(pattern, message, re.IGNORECASE):
                score += rule["priority"] + 2  # 模式匹配权重更高

        if score > best_score:
            best_score = score
            best_intent = rule["name"]

    # 需要达到最低分数阈值
    if best_score >= 6:
        return best_intent

    return None


def extract_content(message: str, intent: str) -> str:
    """从用户消息中提取实际需要处理的内容"""
    content = message

    # 先尝试按冒号/分隔符分割，取后半部分
    separators = r"[:：,，]"
    parts = re.split(separators, content, maxsplit=1)
    if len(parts) > 1:
        after_sep = parts[1].strip()
        # 如果后半部分足够长，优先使用
        if len(after_sep) > 5:
            content = after_sep

    # 移除指令性前缀
    prefixes = [
        r"^(请帮我|帮我|请|麻烦|能不能|可以)\s*",
        r"(润色|修改|优化|改写|生成|提取|整理|总结|概括|提炼|写|做|制作)\s*(以下|下面|这段|这些|这个)?\s*(文本|内容|文字|文章|文献|会议|记录|待办|事项|任务)?\s*",
        r"(以下|下面|这段|这些|这个)\s*(文本|内容|文字|文章|文献|会议|记录)\s*[:：]\s*",
        r"主题[是为约：:]\s*",
    ]
    for prefix in prefixes:
        content = re.sub(prefix, "", content, flags=re.IGNORECASE)
    content = content.strip()
    # 移除占位符提示
    content = re.sub(r"\[.*?\]", "", content)
    return content.strip()


async def route_intent(message: str, files: list, websocket) -> bool:
    """
    意图路由主函数
    返回 True 表示已处理，False 表示交给通用Agent
    """
    intent = detect_intent(message)
    if not intent:
        return False

    content = extract_content(message, intent)

    if not content and intent not in ("ppt", "weekly_report"):
        # 内容为空且不是PPT/周报，交给通用Agent
        return False

    try:
        if intent == "polish":
            await handle_polish(content, websocket)
        elif intent == "ppt":
            await handle_ppt(content, websocket)
        elif intent == "todo":
            await handle_todo(content, websocket)
        elif intent == "meeting":
            await handle_meeting(content, websocket)
        elif intent == "weekly_report":
            await handle_weekly_report(content, websocket)
        elif intent == "summary":
            await handle_summary(content, files, websocket)
        else:
            return False

        return True
    except Exception as e:
        logger.error(f"Intent routing error ({intent}): {e}")
        # 出错时交给通用Agent处理
        return False


async def stream_response(websocket, text: str, msg_type: str = "response"):
    """模拟流式输出文本"""
    await websocket.send_json({"type": "stream_start"})
    # 分块发送，模拟流式效果
    chunk_size = 20
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        await websocket.send_json({"type": "stream_data", "content": chunk})
    await websocket.send_json({"type": "stream_end"})


async def handle_polish(text: str, websocket):
    """处理润色意图"""
    from app.services.document_service import DocumentService

    await websocket.send_json({
        "type": "thinking",
        "title": "✨ 语言润色",
        "content": f"正在润色文本，请稍候..."
    })

    doc_service = DocumentService()
    result = await doc_service.polish_text(text=text, style="academic", language="auto")

    polished = result.get("polished_text", result.get("polished", ""))
    if not polished:
        polished = "润色结果为空，请检查输入内容。"

    # 构建对比展示
    response = f"### ✨ 润色结果\n\n"
    response += f"**原文：**\n{text[:200]}{'...' if len(text) > 200 else ''}\n\n"
    response += f"**润色后（学术风格）：**\n{polished}\n\n"
    response += f"---\n*字数：{len(text)} → {len(polished)}*"

    await stream_response(websocket, response)


async def handle_ppt(topic: str, websocket):
    """处理PPT生成意图"""
    from app.services.document_service import DocumentService

    await websocket.send_json({
        "type": "thinking",
        "title": "📊 PPT生成",
        "content": f"正在生成PPT：{topic}..."
    })

    doc_service = DocumentService()

    # 构建PPT内容
    ppt_content = {
        "引言": [f"{topic}概述", "背景与意义"],
        "核心内容": ["主要观点与分析", "案例研究", "数据支撑"],
        "深入探讨": ["技术路线", "实施方案"],
        "总结": ["关键结论", "未来展望"],
    }

    ppt_bytes = await doc_service.generate_ppt_from_content(
        title=topic or "演示文稿",
        content=ppt_content,
        template="business"
    )

    if ppt_bytes:
        import base64
        b64_data = base64.b64encode(ppt_bytes).decode()

        response = f"### ✅ PPT生成完成\n\n"
        response += f"**文件名：** {topic or '演示文稿'}.pptx\n"
        response += f"**模板：** 商业报告\n"
        response += f"**页数：** 约6页\n\n"
        response += f'<div class="ppt-download-card">'
        response += f'<a href="data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{b64_data}" '
        response += f'download="{topic or "演示文稿"}.pptx" '
        response += f'class="btn btn-primary" style="display:inline-flex;align-items:center;gap:8px;text-decoration:none;padding:12px 24px;">'
        response += f'📥 下载PPT文件</a></div>'

        await stream_response(websocket, response)
    else:
        await stream_response(websocket, "❌ PPT生成失败，请稍后重试。")


async def handle_todo(text: str, websocket):
    """处理待办提取意图"""
    from app.services.document_service import DocumentService

    await websocket.send_json({
        "type": "thinking",
        "title": "✅ 待办提取",
        "content": "正在提取待办事项..."
    })

    doc_service = DocumentService()
    result = await doc_service.extract_todos(text=text)

    todos = result.get("todos", [])
    total = result.get("total", len(todos))

    if todos:
        response = f"### ✅ 待办事项（共{total}项）\n\n"
        for i, todo in enumerate(todos, 1):
            priority_icon = "🔴" if todo.get("priority") == "high" else "🟡" if todo.get("priority") == "medium" else "🟢"
            response += f"{i}. {priority_icon} **{todo.get('task', '')}**\n"
            if todo.get("deadline"):
                response += f"   - ⏰ 截止：{todo['deadline']}\n"
            if todo.get("assignee"):
                response += f"   - 👤 负责人：{todo['assignee']}\n"
            if todo.get("category"):
                response += f"   - 📁 分类：{todo['category']}\n"
            response += "\n"
    else:
        response = "未检测到待办事项。请提供包含任务、截止时间等信息的文本。"

    await stream_response(websocket, response)


async def handle_meeting(text: str, websocket):
    """处理会议纪要意图"""
    from app.services.document_service import DocumentService

    await websocket.send_json({
        "type": "thinking",
        "title": "📝 会议纪要",
        "content": "正在生成会议纪要..."
    })

    doc_service = DocumentService()
    result = await doc_service.generate_meeting_minutes(text=text, output_format="markdown")

    content = ""
    if isinstance(result, dict):
        content = result.get("content", result.get("result", {}).get("content", ""))
    elif isinstance(result, str):
        content = result

    if content:
        await stream_response(websocket, content)
    else:
        await stream_response(websocket, "❌ 会议纪要生成失败，请提供更详细的会议记录。")


async def handle_weekly_report(text: str, websocket):
    """处理周报生成意图"""
    from app.services.document_service import DocumentService

    await websocket.send_json({
        "type": "thinking",
        "title": "📋 周报生成",
        "content": "正在生成周报..."
    })

    doc_service = DocumentService()

    # 从文本中提取工作项
    work_items = []
    if text:
        # 简单按行分割
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:10]:  # 最多10条
            work_items.append({
                "task": line,
                "status": "已完成"
            })

    if not work_items:
        work_items = [{"task": text[:200] if text else "本周工作内容", "status": "已完成"}]

    result = await doc_service.generate_report(
        work_items=work_items,
        report_type="weekly",
        author="用户"
    )

    report = result if isinstance(result, str) else result.get("report", str(result))
    await stream_response(websocket, report)


async def handle_summary(text: str, files: list, websocket):
    """处理文献摘要意图"""
    from app.services.document_service import DocumentService

    await websocket.send_json({
        "type": "thinking",
        "title": "📄 文献摘要",
        "content": "正在生成文献摘要..."
    })

    doc_service = DocumentService()

    # 如果有上传的PDF文件，先解析
    if files:
        for file_info in files:
            if file_info.get("name", "").endswith(".pdf"):
                # PDF文件处理（通过文件路径）
                try:
                    pdf_result = await doc_service.parse_pdf(file_path=file_info.get("path", ""))
                    text = pdf_result.get("text", pdf_result.get("content", text))
                except Exception:
                    pass

    if not text or len(text) < 50:
        await stream_response(websocket, "请提供更详细的文献内容（至少50字），或上传PDF文件。")
        return

    result = await doc_service.summarize_structured(text=text, document_type="academic")

    if isinstance(result, dict):
        response = ""
        if result.get("title"):
            response += f"### 📄 {result['title']}\n\n"
        if result.get("summary"):
            response += f"**摘要：** {result['summary']}\n\n"
        if result.get("key_points"):
            response += "**核心观点：**\n"
            for point in result["key_points"]:
                response += f"- {point}\n"
            response += "\n"
        if result.get("methodology"):
            response += f"**研究方法：** {result['methodology']}\n\n"
        if result.get("conclusion"):
            response += f"**结论：** {result['conclusion']}\n\n"
        if result.get("keywords"):
            response += f"**关键词：** {', '.join(result['keywords'])}\n"
        if not response:
            response = str(result)
    else:
        response = str(result)

    await stream_response(websocket, response)
