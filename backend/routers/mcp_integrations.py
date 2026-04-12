"""
MCP (Model Context Protocol) Server Integration Router

Workspace-level management of external MCP servers.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.database import get_db
from backend.models_db import MCPServer
from backend.lib.id_service import IdService
import httpx
from urllib.parse import urljoin

router = APIRouter(prefix="/mcp-servers", tags=["mcp"])


class MCPServerCreate(BaseModel):
    name: str
    url: str
    transport: str = "sse"          # "sse" | "stdio"
    auth_type: str = "none"         # "api_key" | "bearer" | "none"
    auth_value: Optional[str] = None


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    transport: Optional[str] = None
    auth_type: Optional[str] = None
    auth_value: Optional[str] = None
    is_active: Optional[bool] = None


# --------------- CRUD ---------------

@router.get("")
async def list_mcp_servers(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all MCP servers for the current workspace."""
    workspace_id = get_workspace_context(db, current_user)
    servers = db.query(MCPServer).filter(
        MCPServer.workspace_id == workspace_id
    ).order_by(MCPServer.created_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "transport": s.transport,
            "auth_type": s.auth_type,
            "status": s.status,
            "tools_cache": s.tools_cache,
            "is_active": s.is_active,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in servers
    ]


@router.post("")
async def create_mcp_server(
    data: MCPServerCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new MCP server connection."""
    workspace_id = get_workspace_context(db, current_user)
    
    server = MCPServer(
        id=IdService.generate("mcp"),
        workspace_id=workspace_id,
        name=data.name,
        url=data.url,
        transport=data.transport,
        auth_type=data.auth_type,
        auth_value=data.auth_value,
        status="pending",
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    
    return {
        "id": server.id,
        "name": server.name,
        "url": server.url,
        "transport": server.transport,
        "auth_type": server.auth_type,
        "status": server.status,
        "is_active": server.is_active,
        "created_at": server.created_at,
    }


@router.put("/{server_id}")
async def update_mcp_server(
    server_id: str,
    data: MCPServerUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing MCP server."""
    workspace_id = get_workspace_context(db, current_user)
    server = db.query(MCPServer).filter(
        MCPServer.id == server_id,
        MCPServer.workspace_id == workspace_id
    ).first()
    
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    update_fields = data.model_dump(exclude_none=True)
    for key, value in update_fields.items():
        setattr(server, key, value)
    
    db.commit()
    db.refresh(server)
    return {"status": "updated", "id": server.id}


@router.delete("/{server_id}")
async def delete_mcp_server(
    server_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove an MCP server."""
    workspace_id = get_workspace_context(db, current_user)
    server = db.query(MCPServer).filter(
        MCPServer.id == server_id,
        MCPServer.workspace_id == workspace_id
    ).first()
    
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    db.delete(server)
    db.commit()
    return {"status": "deleted", "id": server_id}


@router.post("/{server_id}/test")
async def test_mcp_server(
    server_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test connectivity to an MCP server and cache available tools."""
    workspace_id = get_workspace_context(db, current_user)
    server = db.query(MCPServer).filter(
        MCPServer.id == server_id,
        MCPServer.workspace_id == workspace_id
    ).first()
    
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    try:
        headers = {}
        if server.auth_type == "bearer" and server.auth_value:
            headers["Authorization"] = f"Bearer {server.auth_value}"
        elif server.auth_type == "api_key" and server.auth_value:
            headers["X-API-Key"] = server.auth_value
        
        # Try connecting to the MCP server endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers["Accept"] = "application/json, text/event-stream"
            
            if server.transport == "sse":
                # With official SDK, we go straight to discovery
                tools = await _discover_mcp_tools(None, server.url, headers)
                if tools:
                    server.status = "connected"
                    server.tools_cache = tools
                else:
                    server.status = "error"
                    return {
                        "status": "error", 
                        "error": f"Failed to discover tools via MCP protocol at {server.url}"
                    }

            else:
                # For stdio servers, just mark as pending (requires local process)
                server.status = "pending"
        
        db.commit()
        return {
            "status": server.status,
            "tools_count": len(server.tools_cache) if server.tools_cache else 0,
            "tools": server.tools_cache,
        }
    except Exception as e:
        server.status = "error"
        db.commit()
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/{server_id}/tools")
async def get_mcp_server_tools(
    server_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cached tools for an MCP server."""
    workspace_id = get_workspace_context(db, current_user)
    server = db.query(MCPServer).filter(
        MCPServer.id == server_id,
        MCPServer.workspace_id == workspace_id
    ).first()
    
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    return {
        "server_id": server.id,
        "server_name": server.name,
        "tools": server.tools_cache or [],
    }


# --------------- Helpers ---------------

async def _discover_mcp_tools(client: httpx.AsyncClient, url: str, headers: dict) -> list:
    """Attempt to discover tools from an MCP server using the MCP protocol via official SDK."""
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    
    # We don't use the injected httpx client since the MCP SDK manages its own HTTPX session internally
    # with the necessary SSE and timeout configurations.
    try:
        async with sse_client(url=url, headers=headers) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else getattr(tool, "parameters", {})
                    }
                    for tool in tools_result.tools
                ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Discovery error: {e}")
    return []

