import asyncio
from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer

db = SessionLocal()
srv = db.query(MCPServer).filter(MCPServer.name.ilike('%Playwright%')).first()
if srv:
    print(f"Old URL: {srv.url}")
    srv.url = "http://localhost:8931/sse"
    db.commit()
    print(f"New URL: {srv.url}")
db.close()
