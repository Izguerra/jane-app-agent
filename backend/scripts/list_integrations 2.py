
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import SessionLocal
from backend.models_db import Integration

def list_integrations():
    try:
        db = SessionLocal()
        integrations = db.query(Integration).filter(Integration.is_active == True).all()
        if not integrations:
            print("No active integrations found.")
        for i in integrations:
            print(f"Workspace: {i.workspace_id} (Type: {type(i.workspace_id)}), Provider: {i.provider}")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_integrations()
