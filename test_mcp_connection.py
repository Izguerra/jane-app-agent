import asyncio
from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer
from livekit.agents.llm.mcp import MCPServerHTTP

async def test():
    db = SessionLocal()
    srv = db.query(MCPServer).filter(MCPServer.name.ilike('%Playwright%')).first()
    db.close()
    if not srv:
        print("Settings not found")
        return
    print(f"Testing URL: {srv.url}, Transport: {srv.transport}")
    
    mcp = MCPServerHTTP(url=srv.url, transport_type=srv.transport or 'sse')
    try:
        await mcp.initialize()
        tools = await mcp.list_tools()
        print(f"Loaded tools: {[t.name for t in tools]}")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
