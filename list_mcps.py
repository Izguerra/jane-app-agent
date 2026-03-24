import asyncio
from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer
import sys

db = SessionLocal()
srvs = db.query(MCPServer).filter(MCPServer.name.ilike('%Playwright%')).all()
for s in srvs:
    print(f"ID: {s.id}, Name: {s.name}, URL: {s.url}")
db.close()
