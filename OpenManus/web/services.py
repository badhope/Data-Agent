"""
业务逻辑服务模块
"""
import asyncio
import re
import sys
import tempfile
import os
from typing import Dict, Any
from .storage import current_settings
from .models import Settings


try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


async def execute_python(code: str, timeout: int = 30) -> Dict[str, Any]:
    """执行Python代码"""
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tempfile.mkdtemp(prefix="dataagent_"),
            env={**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "success": True,
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "returncode": proc.returncode
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def call_llm(prompt: str, settings: Settings) -> str:
    """调用LLM模型"""
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        client = AsyncOpenAI(
            api_key=settings.llm["api_key"],
            base_url=settings.llm["base_url"]
        )
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm["max_tokens"],
            temperature=settings.llm["temperature"],
            top_p=settings.llm["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"


async def clean_text(text: str, rules: Dict[str, Any]) -> str:
    """文本清洗"""
    result = text
    pre_rules = rules.get("pre_processing_rules", [])
    for rule in pre_rules:
        if rule.get("enabled"):
            rule_id = rule.get("id")
            if rule_id == "remove_extra_spaces":
                result = re.sub(r'\s+', ' ', result).strip()
            elif rule_id == "remove_urls_emails":
                result = re.sub(r'https?://\S+', '', result)
                result = re.sub(r'\S+@\S+', '', result)
    return result


async def run_universal_agent(websocket, message: str, settings: Settings = None):
    """运行通用智能体"""
    try:
        if settings is None:
            from .storage import get_settings
            settings = get_settings()
            
        await websocket.send_json({
            "type": "thinking",
            "title": "🤔 理解需求",
            "content": f"正在分析用户需求: {message[:80]}..."
        })

        use_code = False
        kb_related = False
        search_enabled = False

        if settings.knowledge_base.get("enabled"):
            kb_related = any(kw in message.lower() for kw in ["文档", "知识库", "knowledge", "search", "查找"])

        if any(kw in message.lower() for kw in ["代码", "python", "图表", "计算", "数据", "分析", "plot", "chart", "execute"]):
            use_code = True

        if use_code:
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

            result = await execute_python(code, timeout=settings.sandbox["timeout"])

            if result["success"]:
                response = f"✅ 执行成功！\n\n**标准输出:**\n{result['stdout']}\n\n**代码:**\n```python\n{code}\n```"
                if result["stderr"]:
                    response += f"\n\n**警告:**\n{result['stderr']}"
            else:
                response = f"❌ 执行失败: {result.get('error', '未知错误')}\n\n**代码:**\n```python\n{code}\n```"

        elif kb_related:
            await websocket.send_json({
                "type": "thinking",
                "title": "📚 知识库检索",
                "content": "正在从知识库中检索相关信息..."
            })

            from .storage import get_knowledge_bases
            kbs = get_knowledge_bases()
            kb_list = ", ".join([kb.name for kb in kbs.values()])

            await websocket.send_json({
                "type": "thinking",
                "title": "🔍 检索内容",
                "content": f"可用知识库: {kb_list}"
            })

            response = await call_llm(f"用户问题：{message}\n\n可用知识库：{kb_list}\n\n请基于知识库内容回答用户问题。", settings)

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

            response = await call_llm(message, settings)

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

