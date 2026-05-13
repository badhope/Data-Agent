"""
DataAgent - MCP 服务
提供 MCP（Model Context Protocol）工具调用、连接测试、工具列表和资源列表功能
"""

import asyncio
import json
import os

from database import MCPServer


async def _create_mcp_process(server: MCPServer):
    """创建 MCP stdio 子进程的辅助函数"""
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
    return proc


async def execute_mcp_command(server: MCPServer, tool: str, params: dict) -> str:
    """执行 MCP 工具命令"""
    if server.type == "stdio":
        proc = await _create_mcp_process(server)
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


async def test_mcp_connection(server: MCPServer) -> dict:
    """测试 MCP 服务器连接"""
    try:
        if server.type == "stdio":
            proc = await _create_mcp_process(server)
            input_data = json.dumps({"action": "ping"})
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=10.0
            )
            if proc.returncode == 0:
                return {"success": True, "status": "connected", "message": "连接成功"}
            else:
                return {"success": False, "status": "error", "message": stderr.decode()[:200]}
        elif server.type == "sse":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server.url}/health", timeout=10.0)
                if response.status_code == 200:
                    return {"success": True, "status": "connected"}
                else:
                    return {"success": False, "status": "error", "message": f"HTTP {response.status_code}"}
        return {"success": False, "message": "不支持的服务器类型"}
    except asyncio.TimeoutError:
        return {"success": False, "status": "timeout", "message": "连接超时"}
    except Exception as e:
        return {"success": False, "status": "error", "message": str(e)}


async def list_mcp_tools(server: MCPServer) -> dict:
    """获取 MCP 服务器可用工具列表"""
    try:
        if server.type == "stdio":
            proc = await _create_mcp_process(server)
            input_data = json.dumps({"action": "list_tools"})
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=10.0
            )
            if proc.returncode == 0:
                result = json.loads(stdout.decode())
                return {"tools": result.get("tools", [])}
            return {"tools": [], "error": stderr.decode()[:200]}
        elif server.type == "sse":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server.url}/tools", timeout=10.0)
                response.raise_for_status()
                return response.json()
        return {"tools": []}
    except Exception as e:
        return {"tools": [], "error": str(e)}


async def list_mcp_resources(server: MCPServer) -> dict:
    """获取 MCP 服务器可用资源列表"""
    try:
        if server.type == "stdio":
            proc = await _create_mcp_process(server)
            input_data = json.dumps({"action": "list_resources"})
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=10.0
            )
            if proc.returncode == 0:
                result = json.loads(stdout.decode())
                return {"resources": result.get("resources", [])}
            return {"resources": [], "error": stderr.decode()[:200]}
        elif server.type == "sse":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server.url}/resources", timeout=10.0)
                response.raise_for_status()
                return response.json()
        return {"resources": []}
    except Exception as e:
        return {"resources": [], "error": str(e)}
