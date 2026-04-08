import asyncio
import json
import logging
from typing import List, Any
from sqlalchemy.orm import Session
from livekit.agents.llm.mcp import MCPServerHTTP

from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer

logger = logging.getLogger("mcp-loader-service")

class MCPLoaderService:
    # Mapping of Skill Slugs -> MCP Server Names (or name fragments)
    # This allows users to enable "Live Browsing" (advanced-browsing) 
    # and have it map to the "Playwright Browser" MCP server.
    SKILL_MAP = {
        "advanced-browsing": ["Playwright Browser", "Browser"],
        "web-research": ["Context7", "Search"],
        "livekit-debug": ["LiveKit Debugger", "LiveKit Debug"],
        # Worker Mappings
        "lead-research": ["Playwright Browser", "Browser"],
        "competitor-analysis": ["Playwright Browser", "Browser"],
        "content-writer": ["Playwright Browser", "Browser"],
        "job-search": ["Playwright Browser", "Browser"]
    }

    @staticmethod
    async def load_mcp_servers(workspace_id: str, enabled_skill_slugs: List[str] = None) -> tuple[List[Any], List[Any], List[Any]]:
        """
        Loads allowed active MCP servers for the given workspace and agent.
        
        Returns:
            (mcp_tools, mcp_instances, agno_toolkits)
        """
        if enabled_skill_slugs is None:
            logger.info("No enabled skills provided; skipping MCP tool loading for safety.")
            return [], [], []

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
        agno_toolkits = []

        if not mcp_records:
            return mcp_tools, mcp_instances, agno_toolkits

        logger.info(f"Checking {len(mcp_records)} workspace MCP Servers against agent skills: {enabled_skill_slugs}")

        for srv in mcp_records:
            # PERMISSION CHECK
            is_allowed = False
            
            # 1. Check explicit mapping
            for skill_slug, names in MCPLoaderService.SKILL_MAP.items():
                if skill_slug in enabled_skill_slugs:
                    if any(name.lower() in srv.name.lower() for name in names):
                        is_allowed = True
                        break
            
            # 2. Check direct name match (slugified)
            if not is_allowed:
                srv_slug = srv.name.lower().replace(" ", "-")
                if srv_slug in enabled_skill_slugs:
                    is_allowed = True

            if not is_allowed:
                logger.debug(f"Skipping MCP server '{srv.name}' (not enabled in agent capabilities)")
                continue

            try:
                headers = {}
                if srv.auth_type == "bearer" and srv.auth_value:
                    headers["Authorization"] = f"Bearer {srv.auth_value}"
                elif srv.auth_type == "custom" and srv.auth_value:
                    try:
                        custom_headers = json.loads(srv.auth_value)
                        headers.update(custom_headers)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid custom JSON headers for MCP server {srv.id}")

                mcp_instance = MCPServerHTTP(
                    url=srv.url,
                    transport_type=srv.transport or "sse",
                    headers=headers
                )
                
                # Resilient Initialization with Retries and Timeout
                max_retries = 2
                success = False
                for attempt in range(max_retries):
                    try:
                        # 15-second timeout per operation to prevent hanging the vital agent startup but allow slow browsers like Playwright to boot
                        await asyncio.wait_for(mcp_instance.initialize(), timeout=15.0)
                        tools = await asyncio.wait_for(mcp_instance.list_tools(), timeout=15.0)
                        
                        mcp_tools.extend(tools)
                        mcp_instances.append(mcp_instance)
                        
                        # Initialize Agno Toolkit
                        try:
                            if srv.transport == "sse":
                                from agno.tools.mcp import MCPTools
                                from agno.tools.mcp.params import SSEClientParams
                                agno_mcp = MCPTools(
                                    transport="sse",
                                    server_params=SSEClientParams(url=srv.url, headers=headers),
                                    timeout_seconds=15
                                )
                                agno_toolkits.append(agno_mcp)
                        except Exception as e:
                            logger.error(f"Failed to create Agno MCP Toolkit for '{srv.name}': {e}", exc_info=True)

                        logger.info(f"Loaded {len(tools)} tools from MCP server '{srv.name}'")
                        success = True
                        break
                    except asyncio.TimeoutError:
                        logger.warning(f"MCP {srv.name} init timed out (attempt {attempt+1}/{max_retries})")
                        if attempt < max_retries - 1: await asyncio.sleep(1.0)
                    except (ImportError, ModuleNotFoundError):
                        # Handle cases where agno or mcp packages might be missing
                        raise
                    except Exception as e:
                        # Catch specific networking errors that often occur during SSE initialization
                        import httpx
                        import httpcore
                        if isinstance(e, (httpx.ReadError, httpcore.ReadError)):
                            logger.warning(f"MCP {srv.name} connection dropped during init (ReadError) (attempt {attempt+1}/{max_retries})")
                        else:
                            logger.warning(f"MCP {srv.name} init failed (attempt {attempt+1}/{max_retries}): {e}", exc_info=True)
                            
                        if attempt < max_retries - 1: await asyncio.sleep(1.0)
                        
                if not success:
                    logger.error(f"Failed to load tools from MCP Server {srv.id} ({srv.name}) after {max_retries} attempts.")
            except Exception as e:
                logger.error(f"Unexpected error loading MCP Server {srv.id} ({srv.name}): {e}", exc_info=True)

        return mcp_tools, mcp_instances, agno_toolkits

    @staticmethod
    async def cleanup_mcp_servers(mcp_instances: List[Any]):
        """
        Closes long-running SSE connections for active MCP servers when the call terminates.
        """
        for instance in mcp_instances:
            try:
                await instance.aclose()
            except Exception as e:
                logger.warning(f"Error cleaning up MCP server instance: {e}")
