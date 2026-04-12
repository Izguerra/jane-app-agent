import asyncio
import json
import logging
from typing import List, Any, Dict, Optional
from livekit.agents import llm
from livekit.agents.llm.mcp import MCPServerHTTP

from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer

logger = logging.getLogger("mcp-loader-service")

class MCPLoaderService:
    # Mapping of Skill Slugs -> MCP Server Names (or name fragments)
    SKILL_MAP = {
        "advanced-browsing": ["Playwright Browser", "Browser"],
        "web-research": ["Context7", "Search"],
        "livekit-debug": ["LiveKit Debugger", "LiveKit Debug"]
    }

    @staticmethod
    def _is_server_allowed(srv_name: str, enabled_skill_slugs: List[str]) -> bool:
        """Helper to check if a server should be loaded based on enabled skills"""
        # 1. Check explicit mapping
        for skill_slug, names in MCPLoaderService.SKILL_MAP.items():
            if skill_slug in enabled_skill_slugs:
                if any(name.lower() in srv_name.lower() for name in names):
                    return True
        
        # 2. Check direct name match (slugified)
        srv_slug = srv_name.lower().replace(" ", "-")
        return srv_slug in enabled_skill_slugs

    @staticmethod
    def get_cached_mcp_tools(workspace_id: str, enabled_skill_slugs: List[str] = None) -> List[llm.FunctionTool]:
        """
        Retrieves MCP tool definitions from the database cache WITHOUT connecting to the servers.
        This significantly reduces latency for initial agent conversation.
        """
        if not enabled_skill_slugs:
            return []

        db = SessionLocal()
        try:
            mcp_records = db.query(MCPServer).filter(
                MCPServer.workspace_id == workspace_id,
                MCPServer.is_active == True,
                MCPServer.status == "connected"
            ).all()
        finally:
            db.close()

        cached_tools = []
        for srv in mcp_records:
            if not MCPLoaderService._is_server_allowed(srv.name, enabled_skill_slugs):
                continue
            
            if not srv.tools_cache:
                logger.warning(f"MCP Server '{srv.name}' has no tools_cache. Run a sync to enable lazy loading.")
                continue

            # Reconstruct lk.FunctionTool from JSON cache
            # We create a virtual executor that will connect on-demand
            from livekit.agents.llm.tool_context import function_tool

            for tool_def in srv.tools_cache:
                tool_name = tool_def.get("name")
                
                async def lazy_execute(t_name=tool_name, srv_config=srv, **kwargs):
                    logger.info(f"Lazy-initializing MCP Server '{srv_config.name}' for tool '{t_name}'")
                    headers = {}
                    if srv_config.auth_type == "bearer" and srv_config.auth_value:
                        headers["Authorization"] = f"Bearer {srv_config.auth_value}"
                    elif srv_config.auth_type == "custom" and srv_config.auth_value:
                        try: headers.update(json.loads(srv_config.auth_value))
                        except: pass

                    instance = MCPServerHTTP(
                        url=srv_config.url,
                        transport_type=srv_config.transport or "sse",
                        headers=headers
                    )
                    try:
                        await instance.initialize()
                        # This execute calls the underlying MCP server's tool
                        return await instance.execute(t_name, **kwargs)
                    finally:
                        await instance.aclose()

                # Official helper to create FunctionTool from JSON schema
                raw_schema = {
                    "name": tool_name,
                    "description": tool_def.get("description", ""),
                    "parameters": tool_def.get("inputSchema", {})
                }
                ft = function_tool(lazy_execute, raw_schema=raw_schema)
                cached_tools.append(ft)
        
        return cached_tools

    @staticmethod
    async def load_mcp_servers(workspace_id: str, enabled_skill_slugs: List[str] = None) -> tuple[List[Any], List[Any]]:
        """
        Legacy method: Loads allowed active MCP servers for the given workspace and agent.
        Connects immediately (Fast path for Voice/Avatar where latency is already high).
        """
        if enabled_skill_slugs is None:
            return [], []

        db = SessionLocal()
        try:
            mcp_records = db.query(MCPServer).filter(
                MCPServer.workspace_id == workspace_id,
                MCPServer.is_active == True,
                MCPServer.status == "connected"
            ).all()
        finally:
            db.close()

        mcp_tools = []
        mcp_instances = []

        for srv in mcp_records:
            if not MCPLoaderService._is_server_allowed(srv.name, enabled_skill_slugs):
                continue

            try:
                headers = {}
                if srv.auth_type == "bearer" and srv.auth_value:
                    headers["Authorization"] = f"Bearer {srv.auth_value}"
                elif srv.auth_type == "custom" and srv.auth_value:
                    try: headers.update(json.loads(srv.auth_value))
                    except: pass

                mcp_instance = MCPServerHTTP(
                    url=srv.url,
                    transport_type=srv.transport or "sse",
                    headers=headers
                )
                await mcp_instance.initialize()
                tools = await mcp_instance.list_tools()
                
                mcp_tools.extend(tools)
                mcp_instances.append(mcp_instance)
                logger.info(f"Loaded {len(tools)} tools from MCP server '{srv.name}'")
            except Exception as e:
                logger.error(f"Failed to load tools from MCP Server {srv.id} ({srv.name}): {e}")

        return mcp_tools, mcp_instances

    @staticmethod
    async def cleanup_mcp_servers(mcp_instances: List[Any]):
        """Closes long-running SSE connections"""
        for instance in mcp_instances:
            try: await instance.aclose()
            except: pass

