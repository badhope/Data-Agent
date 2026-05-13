"""
MCP服务
提供MCP（Model Context Protocol）工具调用功能
"""

import asyncio
import json
import os

from database import MCPServer


async def execute_mcp_command(server: MCPServer, tool: str, params: dict) -> str:
    if server.type == "stdio":
        cmd = [server.command] + server.args
        env = os.environ.copy()
        env.update(server.env)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        input_data = json.dumps({"tool": tool, "params": params})
        stdout, stderr = await proc.communicate(input=input_data.encode())
        if proc.returncode != 0:
            raise Exception(f"MCP错误: {stderr.decode()}")
        return stdout.decode()
    elif server.type == "sse":
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                server.url,
                json={"tool": tool, "params": params},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("result", "")
    return "不支持的服务器类型"
