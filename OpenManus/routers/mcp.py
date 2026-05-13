"""
DataAgent - MCP 路由
包含 MCP 服务器 CRUD、执行、测试、工具/资源列表等端点
MCP 操作委托给 services 层处理
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import mcp_servers, save_mcp_servers, MCPServer
from services.mcp_service import execute_mcp_command, test_mcp_connection, list_mcp_tools, list_mcp_resources
import uuid

router = APIRouter()


# ==================== MCP 服务器 CRUD ====================

@router.get("/api/mcp/servers")
async def list_mcp_servers():
    return JSONResponse([server.model_dump() for server in mcp_servers.values()])


@router.post("/api/mcp/servers")
async def create_mcp_server(request: Request):
    data = await request.json()
    server_id = data.get("id", str(uuid.uuid4()))
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
async def test_mcp(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    # 委托给 services 层测试连接
    result = await test_mcp_connection(server)
    # 更新服务器状态
    server.status = result.get("status", "unknown")
    save_mcp_servers()
    return JSONResponse(result)


# ==================== MCP 工具/资源/状态 ====================

@router.get("/api/mcp/servers/{server_id}/tools")
async def get_mcp_tools(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    # 委托给 services 层获取工具列表
    result = await list_mcp_tools(server)
    return JSONResponse(result)


@router.get("/api/mcp/servers/{server_id}/resources")
async def get_mcp_resources(server_id: str):
    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail="MCP服务器不存在")
    server = mcp_servers[server_id]
    # 委托给 services 层获取资源列表
    result = await list_mcp_resources(server)
    return JSONResponse(result)


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
