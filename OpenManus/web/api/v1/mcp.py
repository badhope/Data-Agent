"""
MCP API Router
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uuid
from datetime import datetime

from web.models import MCPServer
from web.storage import get_mcp_servers, save_mcp_servers

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

@router.get("/servers")
async def list_mcp_servers():
    """获取所有MCP服务器"""
    servers = get_mcp_servers()
    return JSONResponse([s.model_dump() for s in servers.values()])

@router.post("/servers")
async def create_mcp_server(request: Dict[str, Any]):
    """创建MCP服务器配置"""
    name = request.get("name")
    server_type = request.get("type", "stdio")
    command = request.get("command", "")
    args = request.get("args", [])
    icon = request.get("icon", "🔌")
    
    if not name:
        raise HTTPException(status_code=400, detail="服务器名称不能为空")
    
    server = MCPServer(
        id=str(uuid.uuid4()),
        name=name,
        type=server_type,
        command=command,
        args=args,
        icon=icon,
        enabled=True,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    servers = get_mcp_servers()
    servers[server.id] = server
    save_mcp_servers(servers)
    
    return JSONResponse({"success": True, "server": server.model_dump()})

@router.get("/servers/{server_id}")
async def get_mcp_server(server_id: str):
    """获取单个MCP服务器"""
    servers = get_mcp_servers()
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="服务器不存在")
    return JSONResponse(servers[server_id].model_dump())

@router.delete("/servers/{server_id}")
async def delete_mcp_server(server_id: str):
    """删除MCP服务器配置"""
    servers = get_mcp_servers()
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    del servers[server_id]
    save_mcp_servers(servers)
    
    return JSONResponse({"success": True})

@router.post("/servers/{server_id}/toggle")
async def toggle_mcp_server(server_id: str):
    """切换MCP服务器启用状态"""
    servers = get_mcp_servers()
    if server_id not in servers:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    server = servers[server_id]
    server.enabled = not server.enabled
    server.updated_at = datetime.now().isoformat()
    
    servers[server_id] = server
    save_mcp_servers(servers)
    
    return JSONResponse({"success": True, "server": server.model_dump()})
