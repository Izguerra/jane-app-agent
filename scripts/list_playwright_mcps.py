import asyncio
from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer
import sys

def main():
    try:
        db = SessionLocal()
        srvs = db.query(MCPServer).filter(MCPServer.name.ilike('%Playwright%')).all()
        for s in srvs:
            print(f"ID: {s.id}, Name: {s.name}, URL: {s.url}, Auth: {s.auth_type}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
