import asyncio
from backend.database import SessionLocal
from backend.database.models.workspace import MCPServer
import sys

def main():
    try:
        db = SessionLocal()
        srv = db.query(MCPServer).filter(MCPServer.name.ilike('%Playwright%')).first()
        if srv:
            print(f"Old URL: {srv.url}")
            srv.url = "http://localhost:8931/sse"
            db.commit()
            print(f"New URL: {srv.url}")
        else:
            print("Server not found")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
