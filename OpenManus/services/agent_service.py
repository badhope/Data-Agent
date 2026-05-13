"""
DataAgent - Agent 服务
提供意图检测和通用 Agent 运行功能，整合 LLM 调用、代码执行和知识库检索
"""

import asyncio
import re

from fastapi import WebSocket

from database import current_settings, knowledge_bases
from services.llm_service import call_llm, execute_python


def detect_intent(message: str) -> dict:
    """
    检测用户消息的意图，返回意图分类结果
    返回: {"use_code": bool, "kb_related": bool, "search_enabled": bool}
    """
    use_code = False
    kb_related = False

    # 检测知识库相关意图
    if current_settings.knowledge_base.get("enabled"):
        kb_related = any(
            kw in message.lower()
            for kw in ["文档", "知识库", "knowledge", "search", "查找"]
        )

    # 检测代码/数据分析意图
    if any(kw in message.lower() for kw in [
        "代码", "python", "图表", "计算", "数据", "分析", "plot", "chart", "execute"
    ]):
        use_code = True

    return {
        "use_code": use_code,
        "kb_related": kb_related,
        "search_enabled": False
    }


async def run_universal_agent(websocket: WebSocket, message: str):
    """运行通用 Agent，根据意图自动选择处理方式"""
    try:
        await websocket.send_json({
            "type": "thinking",
            "title": "🤔 理解需求",
            "content": f"正在分析用户需求: {message[:80]}..."
        })

        intent = detect_intent(message)

        if intent["use_code"]:
            await websocket.send_json({
                "type": "thinking",
                "title": "🛠️ 工具选择",
                "content": "检测到代码/数据需求，准备生成Python代码"
            })

            code_prompt = f"""根据用户需求生成Python代码：
用户需求：{message}
请直接输出可执行的Python代码，不需要解释。如果需要图表，保存为PNG文件。"""

            await websocket.send_json({
                "type": "thinking",
                "title": "💬 调用模型",
                "content": "正在向AI模型请求生成代码..."
            })

            code = await call_llm(code_prompt, current_settings)
            code = re.sub(r'^```python\s*\n?', '', code.strip(), flags=re.MULTILINE)
            code = re.sub(r'\n?```$', '', code.strip(), flags=re.MULTILINE)
            code = code.strip()

            await websocket.send_json({
                "type": "thinking",
                "title": "📋 生成代码",
                "content": f"```python\n{code}\n```"
            })

            await websocket.send_json({
                "type": "thinking",
                "title": "▶️ 执行代码",
                "content": "正在沙箱环境中执行代码..."
            })

            result = await execute_python(code, timeout=current_settings.sandbox["timeout"])

            if result["success"]:
                response = f"✅ 执行成功！\n\n**标准输出:**\n{result['stdout']}\n\n**代码:**\n```python\n{code}\n```"
                if result["stderr"]:
                    response += f"\n\n**警告:**\n{result['stderr']}"
            else:
                response = f"❌ 执行失败: {result.get('error', '未知错误')}\n\n**代码:**\n```python\n{code}\n```"

        elif intent["kb_related"] and knowledge_bases:
            await websocket.send_json({
                "type": "thinking",
                "title": "📚 知识库检索",
                "content": "正在从知识库中检索相关信息..."
            })

            kb_list = ", ".join([kb.name for kb in knowledge_bases.values()])

            await websocket.send_json({
                "type": "thinking",
                "title": "🔍 检索内容",
                "content": f"可用知识库: {kb_list}"
            })

            response = await call_llm(
                f"用户问题：{message}\n\n可用知识库：{kb_list}\n\n请基于知识库内容回答用户问题。",
                current_settings
            )

        else:
            await websocket.send_json({
                "type": "thinking",
                "title": "🧠 智能分析",
                "content": "正在处理您的请求..."
            })

            await websocket.send_json({
                "type": "thinking",
                "title": "💬 调用模型",
                "content": "正在向AI模型发送请求..."
            })

            response = await call_llm(message, current_settings)

        # 流式输出结果
        await websocket.send_json({"type": "stream_start"})
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            await websocket.send_json({"type": "stream_data", "content": chunk})
            await asyncio.sleep(0.05)
        await websocket.send_json({"type": "stream_end"})

    except Exception as e:
        error_msg = f"❌ 处理失败: {str(e)[:300]}"
        await websocket.send_json({"type": "error", "content": error_msg})
        import traceback
        print(f"Error in run_universal_agent: {traceback.format_exc()}")
