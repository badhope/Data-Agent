"""
业务逻辑服务模块
"""
import asyncio
import re
import sys
import tempfile
import os
import json
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
    """改进的智能体，优先使用泰迪杯B题功能"""
    try:
        if settings is None:
            from .storage import get_settings
            settings = get_settings()
            
        await websocket.send_json({
            "type": "thinking",
            "title": "🤔 理解需求",
            "content": f"正在分析: {message[:60]}..."
        })

        # 优先使用泰迪杯B题功能处理财务相关查询
        tidycup_used = False
        try:
            from pathlib import Path
            import sys
            BASE_DIR = Path(__file__).parent.parent
            sys.path.insert(0, str(BASE_DIR))
            
            # 财务关键词检测
            financial_keywords = ["贵州茅台", "平安银行", "中国平安", "财务", 
                               "净利润", "营收", "资产", "负债", "利润", 
                               "报表", "白酒", "银行", "保险", "对比", 
                               "趋势", "2023", "2022", "分析"]
            
            is_financial = any(kw in message for kw in financial_keywords)
            
            if is_financial:
                await websocket.send_json({
                    "type": "thinking",
                    "title": "📊 泰迪杯B题系统",
                    "content": "正在使用专业财务分析系统..."
                })
                
                # 尝试导入并使用
                from web.tidycup import FullTidyCupPipeline
                db_path = BASE_DIR / "data" / "tidycup.db"
                pipeline = FullTidyCupPipeline(db_path)
                pipeline.initialize()
                
                result = await pipeline.process_complex_query(message)
                
                # 构建友好的响应
                response_parts = ["### 📊 财务分析结果\n\n"]
                
                # 任务计划
                if result.get("task_plan") and result["task_plan"].get("sub_tasks"):
                    tasks = result["task_plan"]["sub_tasks"]
                    response_parts.append("**执行计划:**\n")
                    for task in tasks[:3]:
                        response_parts.append(f"- {task.get('description', '')}\n")
                    response_parts.append("\n")
                
                # RAG结果
                if result.get("rag_results"):
                    docs = result["rag_results"]
                    response_parts.append("**📚 参考文档:**\n")
                    for i, doc in enumerate(docs[:3], 1):
                        meta = doc.get('metadata', {})
                        content = doc.get('content', '')
                        response_parts.append(f"{i}. {content[:150]}...\n")
                        if meta.get('company'):
                            response_parts.append(f"   *来源: {meta.get('company')} {meta.get('year', '')}*\n")
                    response_parts.append("\n")
                
                # SQL结果
                if result.get("sql_result"):
                    sql_res = result["sql_result"]
                    if sql_res.get("success") and sql_res.get("result"):
                        response_parts.append("**💾 数据库数据:**\n```json\n")
                        # 格式化显示数据
                        for row in sql_res["result"][:5]:
                            response_parts.append(f"{json.dumps(row, ensure_ascii=False)}\n")
                        if len(sql_res["result"]) > 5:
                            response_parts.append(f"... (共{len(sql_res['result'])}条)\n")
                        response_parts.append("```\n")
                
                # 归因信息
                if result.get("attribution"):
                    response_parts.append(f"**📖 分析来源:** {result['attribution'].get('summary', '')}\n")
                
                # 流式发送响应
                final_response = "".join(response_parts)
                await websocket.send_json({"type": "stream_start"})
                chunk_size = 50
                for i in range(0, len(final_response), chunk_size):
                    chunk = final_response[i:i + chunk_size]
                    await websocket.send_json({"type": "stream_data", "content": chunk})
                    await asyncio.sleep(0.03)
                await websocket.send_json({"type": "stream_end"})
                tidycup_used = True
                
        except Exception as e:
            import traceback
            print(f"Tidycup error: {e}")
            print(traceback.format_exc())

        # 如果泰迪杯功能没处理，继续用通用逻辑
        if not tidycup_used:
            use_code = any(kw in message.lower() for kw in ["代码", "python", "图表", "plot", "chart", "execute"])
            
            if use_code:
                await websocket.send_json({
                    "type": "thinking",
                    "title": "💻 代码分析",
                    "content": "正在准备执行代码..."
                })
                
                code = f"print('分析查询: {message[:50]}')"
                result = await execute_python(code, timeout=settings.sandbox["timeout"])
                
                response = f"✅ 代码执行：\n输出: {result.get('stdout', '')}\n{result.get('stderr', '')}"
            else:
                await websocket.send_json({
                    "type": "thinking",
                    "title": "🧠 智能处理",
                    "content": "正在处理您的请求..."
                })
                
                # 简单的内置回复，避免依赖LLM
                if "你好" in message or "hello" in message.lower():
                    response = "你好！我是DATA-AI智能助手。我可以帮你进行财务数据分析、代码执行和知识问答。有什么我可以帮你的吗？"
                elif "帮助" in message or "help" in message.lower():
                    response = """我可以帮助你：
1. 📊 财务数据分析（泰迪杯B题功能）
2. 💻 执行Python代码
3. 📚 知识库问答
试试问我：贵州茅台2023年财务数据"""
                else:
                    response = f"收到您的消息：{message}。这是一个演示回复。在实际使用中，请配置API Key以获得更强大的功能。"

            # 流式发送响应
            await websocket.send_json({"type": "stream_start"})
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                await websocket.send_json({"type": "stream_data", "content": chunk})
                await asyncio.sleep(0.03)
            await websocket.send_json({"type": "stream_end"})

    except Exception as e:
        error_msg = f"❌ 处理失败: {str(e)[:300]}"
        await websocket.send_json({"type": "error", "content": error_msg})
        import traceback
        print(f"Agent error: {traceback.format_exc()}")
