"""
DataAgent - 增强型 Agent 服务
基于 ReAct (Reasoning + Acting) 模式的智能 Agent
支持多步推理、工具调用、流式思考展示
"""

import asyncio
import json
import re
from typing import List, Optional, Callable

from fastapi import WebSocket

from database import current_settings, knowledge_bases, documents
from services.llm_service import call_llm, execute_python
from routers.feedback import get_learned_system_prompt_suffix


class WebAgent:
    """
    基于 ReAct 模式的 Web Agent
    支持: 多步推理、工具调用、知识库检索、代码执行
    """

    def __init__(self, websocket: WebSocket, settings: dict):
        self.websocket = websocket
        self.settings = settings
        self.messages: List[dict] = []  # 对话历史
        self.max_steps = settings.get("agent", {}).get("max_steps", 10)
        self.step_count = 0
        self.tools = self._build_tools()

    def _build_tools(self) -> list:
        """构建可用工具列表"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "python_execute",
                    "description": "执行Python代码。适用于数据分析、图表生成、计算、文件操作等任务。代码中的print输出会被捕获返回。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要执行的Python代码"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "代码的简要说明"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "搜索知识库中的相关文档内容。当用户询问关于已上传文档的问题时使用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词或问题"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish",
                    "description": "当任务完成时调用此工具来结束对话。提供一个最终的总结回复。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "任务完成的总结回复"
                            }
                        },
                        "required": ["summary"]
                    }
                }
            }
        ]
        return tools

    async def send_thinking(self, title: str, content: str):
        """发送思考步骤到前端"""
        await self.websocket.send_json({
            "type": "thinking",
            "title": title,
            "content": content
        })

    async def send_stream(self, text: str):
        """流式发送文本"""
        await self.websocket.send_json({"type": "stream_start"})
        chunk_size = 30
        for i in range(0, len(text), chunk_size):
            await self.websocket.send_json({"type": "stream_data", "content": text[i:i + chunk_size]})
            await asyncio.sleep(0.03)
        await self.websocket.send_json({"type": "stream_end"})

    async def send_error(self, message: str):
        await self.websocket.send_json({"type": "error", "content": message})

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """执行工具调用"""
        if tool_name == "python_execute":
            code = arguments.get("code", "")
            explanation = arguments.get("explanation", "")

            await self.send_thinking("▶️ 执行代码", f"{explanation}\n```python\n{code[:500]}{'...' if len(code) > 500 else ''}\n```")

            timeout = self.settings.get("sandbox", {}).get("timeout", 60)
            result = await execute_python(code, timeout=timeout)

            if result["success"]:
                output = result["stdout"]
                if result["stderr"]:
                    output += f"\n[警告] {result['stderr']}"
                return f"执行成功。输出:\n{output}" if output else "执行成功，无输出。"
            else:
                return f"执行失败: {result.get('error', '未知错误')}"

        elif tool_name == "search_knowledge_base":
            query = arguments.get("query", "")

            if not knowledge_bases:
                return "没有可用的知识库。请先在知识库管理中创建知识库并上传文档。"

            await self.send_thinking("📚 搜索知识库", f"正在搜索: {query}")

            # 搜索所有知识库
            all_results = []
            for kb_id, kb in knowledge_bases.items():
                try:
                    from services.knowledge_service import search_knowledge_base
                    results = await search_knowledge_base(kb_id, query, top_k=3)
                    for r in results:
                        r["kb_name"] = kb.name
                    all_results.extend(results)
                except Exception as e:
                    all_results.append({"content": f"搜索知识库 '{kb.name}' 失败: {str(e)}", "score": 0})

            if not all_results:
                return f"在知识库中未找到与 '{query}' 相关的内容。"

            # 按相关度排序
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

            # 格式化结果
            formatted = []
            for r in all_results[:5]:
                kb_name = r.get("kb_name", "未知")
                content = r.get("content", "")[:300]
                score = r.get("score", 0)
                formatted.append(f"[{kb_name}] (相关度: {score:.2f})\n{content}")

            return "知识库搜索结果:\n" + "\n---\n".join(formatted)

        elif tool_name == "finish":
            return f"__FINISH__:{arguments.get('summary', '任务完成。')}"

        return f"未知工具: {tool_name}"

    async def run(self, message: str):
        """运行 Agent 的主循环"""
        try:
            # 检查 API Key 是否配置
            api_key = self.settings.get("llm", {}).get("api_key", "")
            if not api_key:
                await self.send_error(
                    "⚠️ 未配置 API Key\n\n"
                    "点击左上角 ☰ → 设置 → 填入 API Key"
                )
                return

            # 添加用户消息到历史
            self.messages.append({"role": "user", "content": message})

            # Step 1: 理解需求
            await self.send_thinking("🧠 分析需求", f"正在理解用户需求并制定执行计划...")

            # 构建系统提示
            system_prompt = self._build_system_prompt()

            # Step 2: ReAct 循环
            final_response = None

            while self.step_count < self.max_steps:
                self.step_count += 1

                # Think: 决定下一步行动
                await self.send_thinking(
                    f"💭 思考步骤 {self.step_count}/{self.max_steps}",
                    f"分析当前状态，决定下一步行动..."
                )

                # 调用 LLM 进行推理
                think_result = await self._llm_with_tools(system_prompt)

                if think_result.get("error"):
                    # 如果工具调用失败，直接用纯文本模式
                    await self.send_thinking("💬 生成回复", "使用直接回复模式...")
                    response = await call_llm(message if self.step_count == 1 else self._get_context_summary(), self.settings)
                    self.messages.append({"role": "assistant", "content": response})
                    await self.send_stream(response)
                    return

                content = think_result.get("content", "")
                tool_calls = think_result.get("tool_calls", [])

                if not tool_calls:
                    # 没有工具调用，直接回复
                    if content:
                        await self.send_thinking("✨ 生成回复", "任务完成，生成最终回复...")
                        self.messages.append({"role": "assistant", "content": content})
                        await self.send_stream(content)
                        return
                    else:
                        # 没有内容也没有工具调用，结束
                        break

                # Act: 执行工具调用
                for tool_call in tool_calls:
                    func_name = tool_call.get("function", {}).get("name", "")
                    func_args_str = tool_call.get("function", {}).get("arguments", "{}")

                    try:
                        func_args = json.loads(func_args_str) if isinstance(func_args_str, str) else func_args_str
                    except json.JSONDecodeError:
                        func_args = {}

                    # 执行工具
                    tool_result = await self.call_tool(func_name, func_args)

                    # 检查是否结束
                    if tool_result.startswith("__FINISH__:"):
                        final_response = tool_result.replace("__FINISH__:", "", 1)
                        break

                    # 添加工具结果到消息历史
                    self.messages.append({
                        "role": "assistant",
                        "content": content,
                        "tool_calls": [tool_call]
                    })
                    self.messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call.get("id", ""),
                        "name": func_name
                    })

                    await self.send_thinking(
                        f"📋 工具结果 ({func_name})",
                        tool_result[:300] + ("..." if len(tool_result) > 300 else "")
                    )

                if final_response:
                    self.messages.append({"role": "assistant", "content": final_response})
                    await self.send_stream(final_response)
                    return

            # 超过最大步数，生成总结
            if not final_response:
                await self.send_thinking("📝 总结", "已达到最大步数，生成总结...")
                summary_prompt = f"请基于以下对话历史，给出一个简洁的总结回复:\n\n" + "\n".join(
                    f"{m['role']}: {m['content'][:200]}" for m in self.messages[-10:]
                )
                summary = await call_llm(summary_prompt, self.settings)
                self.messages.append({"role": "assistant", "content": summary})
                await self.send_stream(summary)

        except Exception as e:
            import traceback
            print(f"Agent error: {traceback.format_exc()}")
            await self.send_error(f"处理失败: {str(e)[:300]}")

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        base_prompt = f"""你是 DataAgent 智能助手，一个强大的 AI Agent。

## 你的能力
1. **代码执行**: 通过 python_execute 工具执行 Python 代码，支持数据分析、图表生成、文件操作等
2. **知识库检索**: 通过 search_knowledge_base 工具搜索已上传的文档
3. **直接回答**: 对于简单问题，可以直接回复，无需使用工具

## 工作方式
- 分析用户需求，判断是否需要使用工具
- 如果需要代码执行或数据分析，使用 python_execute 工具
- 如果需要查询文档，使用 search_knowledge_base 工具
- 完成任务后，使用 finish 工具结束并提供总结
- 你可以多次调用工具来完成复杂任务

## 注意事项
- 执行代码时，确保代码正确且安全
- 如果代码执行失败，分析错误原因并尝试修复
- 回复时使用 Markdown 格式，代码使用代码块
- 用中文回复用户"""

        # 追加基于用户反馈自动学习的偏好提示
        learned_suffix = get_learned_system_prompt_suffix()
        if learned_suffix:
            return base_prompt + learned_suffix
        return base_prompt

    def _get_context_summary(self) -> str:
        """获取对话上下文摘要"""
        recent = self.messages[-6:]
        return "\n".join(f"{m['role']}: {m['content'][:300]}" for m in recent)

    async def _llm_with_tools(self, system_prompt: str) -> dict:
        """调用 LLM 并解析工具调用"""
        try:
            from openai import AsyncOpenAI

            api_key = self.settings["llm"].get("api_key", "")
            base_url = self.settings["llm"].get("base_url", "https://api.openai.com/v1")
            model = self.settings["llm"].get("model", "gpt-4o")
            temperature = self.settings["llm"].get("temperature", 0.7)
            max_tokens = self.settings["llm"].get("max_tokens", 4096)

            if not api_key:
                return {"error": "未配置 API Key"}

            client = AsyncOpenAI(api_key=api_key, base_url=base_url)

            # 构建消息列表
            api_messages = [{"role": "system", "content": system_prompt}]

            # 添加对话历史（限制长度避免 token 超限）
            context_messages = self.messages[-20:]  # 最近20条消息
            for msg in context_messages:
                api_msg = {"role": msg["role"]}
                if msg["role"] == "tool":
                    api_msg["content"] = msg.get("content", "")
                    api_msg["tool_call_id"] = msg.get("tool_call_id", "")
                    api_msg["name"] = msg.get("name", "")
                else:
                    api_msg["content"] = msg.get("content", "")
                    if "tool_calls" in msg and msg["tool_calls"]:
                        api_msg["tool_calls"] = msg["tool_calls"]
                api_messages.append(api_msg)

            response = await client.chat.completions.create(
                model=model,
                messages=api_messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=temperature,
                max_tokens=max_tokens
            )

            choice = response.choices[0]
            result = {
                "content": choice.message.content or "",
                "tool_calls": []
            }

            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    result["tool_calls"].append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })

            return result

        except Exception as e:
            print(f"LLM tool call error: {e}")
            return {"error": str(e)}


# 保持向后兼容的函数接口
async def run_universal_agent(websocket: WebSocket, message: str):
    """运行通用 Agent（增强版 ReAct 模式）"""
    agent = WebAgent(websocket, current_settings.model_dump())
    await agent.run(message)
