import asyncio
import json
from backend.database import SessionLocal
from backend.models_db import MCPServer
from backend.routers.mcp_integrations import _discover_mcp_tools

async def resync_mcp():
    db = SessionLocal()
    try:
        srv = db.query(MCPServer).filter(MCPServer.id == "mcp_000VCwxjHA1QAKN7yIiX8OKjgFp").first()
        if not srv:
            print("Server not found")
            return
            
        print(f"Resyncing {srv.name}...")
        headers = {}
        if srv.auth_type == "bearer" and srv.auth_value:
            headers["Authorization"] = f"Bearer {srv.auth_value}"
        
        tools = await _discover_mcp_tools(None, srv.url, headers)
        if tools:
            srv.tools_cache = tools
            srv.status = "connected"
            db.commit()
            print(f"Successfully cached {len(tools)} tools with schemas.")
            # Verify one tool
            print(f"Sample tool: {json.dumps(tools[0], indent=2)}")
        else:
            print("No tools found during discovery.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(resync_mcp())
