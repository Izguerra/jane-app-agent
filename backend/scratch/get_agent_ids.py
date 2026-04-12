import os
from sqlalchemy import create_url
from sqlalchemy.orm import sessionmaker
from backend.database import SessionLocal, engine
from backend.models_db import Agent, Workspace

def get_ids():
    db = SessionLocal()
    try:
        workspaces = db.query(Workspace).all()
        for ws in workspaces:
            print(f"Workspace: {ws.id} - {ws.name}")
            agents = db.query(Agent).filter(Agent.workspace_id == ws.id).all()
            for agent in agents:
                 print(f"  Agent: {agent.id} - {agent.name}")
    finally:
        db.close()

if __name__ == "__main__":
    get_ids()
