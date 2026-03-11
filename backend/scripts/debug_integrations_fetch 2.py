"""
Debug Integrations Fetch
Mimic the router's logic for fetching integrations.
"""
import sys
import os
import json

# Add backend to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Integration, Workspace

TEAM_ID = "org_000V7dMzThAVrPNF3XBlRXq4MO"  # From previous inspection

def debug_fetch():
    db = SessionLocal()
    try:
        print(f"Fetching for Team ID: {TEAM_ID}")
        
        # 1. Get Workspace (Logic from router)
        workspace = db.query(Workspace).filter(Workspace.team_id == TEAM_ID).first()
        
        if not workspace:
            print("ERROR: No workspace found for team!")
            return

        print(f"Resolved Workspace: {workspace.id} ({workspace.name})")

        # 2. Get Integrations (Logic from router)
        integrations = db.query(Integration).filter(Integration.workspace_id == workspace.id).all()
        
        print(f"Found {len(integrations)} integrations.")
        for i in integrations:
            print(f"- Provider: {i.provider}, Active: {i.is_active}, ID: {i.id}")
            print(f"  Settings: {i.settings}")
            if i.settings:
                try:
                    parsed = json.loads(i.settings)
                    print("  Settings parse: OK")
                except:
                    print("  Settings parse: FAILED")
                    
    finally:
        db.close()

if __name__ == "__main__":
    debug_fetch()
