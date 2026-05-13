"""
DataAgent - MCP 路由
包含 MCP 服务器 CRUD、执行、测试、工具/资源列表等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import mcp_servers, save_mcp_servers, MCPServer
import json, os, asyncio

router = APIRouter()


# ==================== MCP 服务器 CRUD ====================

@router.get("/api/mcp/servers")
async def list_mcp_servers():
    return JSONResponse([server.model_dump() for server in mcp_servers.values()])


@router.post("/api/mcp/servers")
async def create_mcp_server(request: Request):
    data = await request.json()
    server_id = data.get("id", str(__import__('uuid').uuid4()))
    server = MCPServer(
        id=server_id,
        name=data.get("name", "未命名服务器"),
        type=data.get("type", "stdio"),
        command=data.get("command", ""),
        args=data.get("args", []),
        url=data.get("url", ""),
        env=data.get("env", {}),
        enabled=data.get("enabled", True),
        icon=data.get("icon", "🔌")
    )
    mcp_servers[server_id] = server
    save_mcp_servers()
    return JSONResponse(server.model_dump())


@router.put("/api/mcp/servers/{server_id}")
async def update_mcp_server(server_id: str, request: Request):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    data = await request.json()
    server = mcp_servers[server_id]
    server.name = data.get("name", server.name)
    server.type = data.get("type", server.type)
    server.command = data.get("command", server.command)
    server.args = data.get("args", server.args)
    server.url = data.get("url", server.url)
    server.env = data.get("env", server.env)
    server.enabled = data.get("enabled", server.enabled)
    save_mcp_servers()
    return JSONResponse(server.model_dump())


@router.delete("/api/mcp/servers/{server_id}")
async def delete_mcp_server(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    del mcp_servers[server_id]
    save_mcp_servers()
    return JSONResponse({"success": True, "message": "MCP服务器已删除"})


# ==================== MCP 执行 ====================

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


@router.post("/api/mcp/servers/{server_id}/execute")
async def execute_mcp_tool(server_id: str, request: Request):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    if not server.enabled:
        raise HTTPException(status_code=400, detail="MCP服务器已禁用")
    data = await request.json()
    tool_name = data.get("tool", "")
    params = data.get("parameters", {})
    try:
        result = await execute_mcp_command(server, tool_name, params)
        return JSONResponse({"success": True, "result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP执行失败: {str(e)}")


# ==================== MCP 测试连接 ====================

@router.post("/api/mcp/servers/{server_id}/test")
async def test_mcp_connection(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    try:
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
            input_data = json.dumps({"action": "ping"})
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=10.0
            )
            if proc.returncode == 0:
                server.status = "connected"
                save_mcp_servers()
                return JSONResponse({"success": True, "status": "connected", "message": "连接成功"})
            else:
                server.status = "error"
                save_mcp_servers()
                return JSONResponse({"success": False, "status": "error", "message": stderr.decode()[:200]})
        elif server.type == "sse":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server.url}/health", timeout=10.0)
                if response.status_code == 200:
                    server.status = "connected"
                    save_mcp_servers()
                    return JSONResponse({"success": True, "status": "connected"})
                else:
                    server.status = "error"
                    save_mcp_servers()
                    return JSONResponse({"success": False, "status": "error", "message": f"HTTP {response.status_code}"})
        return JSONResponse({"success": False, "message": "不支持的服务器类型"})
    except asyncio.TimeoutError:
        server.status = "timeout"
        save_mcp_servers()
        return JSONResponse({"success": False, "status": "timeout", "message": "连接超时"})
    except Exception as e:
        server.status = "error"
        save_mcp_servers()
        return JSONResponse({"success": False, "status": "error", "message": str(e)})


# ==================== MCP 工具/资源/状态 ====================

@router.get("/api/mcp/servers/{server_id}/tools")
async def get_mcp_tools(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    try:
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
            input_data = json.dumps({"action": "list_tools"})
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=10.0
            )
            if proc.returncode == 0:
                result = json.loads(stdout.decode())
                return JSONResponse({"tools": result.get("tools", [])})
            return JSONResponse({"tools": [], "error": stderr.decode()[:200]})
        elif server.type == "sse":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server.url}/tools", timeout=10.0)
                response.raise_for_status()
                return JSONResponse(response.json())
        return JSONResponse({"tools": []})
    except Exception as e:
        return JSONResponse({"tools": [], "error": str(e)})


@router.get("/api/mcp/servers/{server_id}/resources")
async def get_mcp_resources(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    try:
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
            input_data = json.dumps({"action": "list_resources"})
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=10.0
            )
            if proc.returncode == 0:
                result = json.loads(stdout.decode())
                return JSONResponse({"resources": result.get("resources", [])})
            return JSONResponse({"resources": [], "error": stderr.decode()[:200]})
        elif server.type == "sse":
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server.url}/resources", timeout=10.0)
                response.raise_for_status()
                return JSONResponse(response.json())
        return JSONResponse({"resources": []})
    except Exception as e:
        return JSONResponse({"resources": [], "error": str(e)})


@router.get("/api/mcp/servers/{server_id}/status")
async def get_mcp_status(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    return JSONResponse({
        "id": server.id,
        "name": server.name,
        "status": server.status or "unknown",
        "enabled": server.enabled,
        "type": server.type
    })
