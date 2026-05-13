"""
DataAgent - LLM 调用服务
提供 Python 代码执行、LLM 模型调用、JSON 解析和连接测试功能
所有 LLM 相关调用统一通过此模块
"""

import asyncio
import json
import re
import sys
import os
import tempfile

from config import OPENAI_AVAILABLE


async def execute_python(code: str, timeout: int = 30) -> dict:
    """在沙箱中执行 Python 代码"""
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


async def call_llm(prompt: str, settings) -> str:
    """调用 LLM 模型（仅 user 消息）"""
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        from openai import AsyncOpenAI
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


async def call_llm_with_system(system_prompt: str, user_prompt: str, settings) -> str:
    """调用 LLM 模型（带 system 消息）"""
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.llm["api_key"],
            base_url=settings.llm["base_url"]
        )
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.llm["max_tokens"],
            temperature=settings.llm["temperature"],
            top_p=settings.llm["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"


async def call_llm_json(prompt: str, settings, pattern: str = r'\{.*\}|\[.*\]', temperature: float = None) -> dict:
    """调用 LLM 并解析 JSON 响应，用于 skills/agent/nl2sql 等路由"""
    if not OPENAI_AVAILABLE:
        return {"error": "未安装 openai 库，请运行 pip install openai"}
    if not settings.llm.get("api_key"):
        return {"error": "请先在设置中配置 API Key"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.llm["api_key"],
            base_url=settings.llm["base_url"]
        )
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm.get("max_tokens", 1000),
            temperature=temperature if temperature is not None else settings.llm.get("temperature", 0.3)
        )
        result_text = response.choices[0].message.content.strip()
        # 尝试从响应中提取 JSON
        json_match = re.search(pattern, result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"error": "AI返回格式无法解析", "raw": result_text}
    except json.JSONDecodeError as e:
        return {"error": f"JSON解析失败: {str(e)}"}
    except Exception as e:
        return {"error": f"LLM调用失败: {str(e)}"}


async def test_connection(api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o") -> dict:
    """测试 LLM 连接是否正常"""
    if not api_key:
        return {"success": False, "message": "API Key 不能为空"}
    if not OPENAI_AVAILABLE:
        return {"success": False, "message": "未安装 openai 库"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}
