"""
Inspect Integrations
"""
import sys
import os
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Integration, Workspace

def inspect_integrations():
    db = SessionLocal()
    try:
        print("\n--- Workspaces ---")
        workspaces = db.query(Workspace).all()
        for w in workspaces:
            print(f"Workspace: {w.name} (ID: {w.id}, Team: {w.team_id})")

        print("\n--- Integrations ---")
        integrations = db.query(Integration).all()
        for i in integrations:
            print(f"ID: {i.id} | Workspace: {i.workspace_id} | Provider: {i.provider} | Active: {i.is_active}")
            print(f"Settings: {i.settings}")
            print("-" * 20)
            
    finally:
        db.close()

if __name__ == "__main__":
    inspect_integrations()
