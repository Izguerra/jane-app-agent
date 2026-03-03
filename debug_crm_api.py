
import os
import sys
from sqlalchemy import create_engine, text, func, desc
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.getcwd())

from backend.models_db import Customer, Communication, Workspace, AgentSettings, Team
from backend.services.crm_service import CRMService

load_dotenv()

from backend.database import SessionLocal

def test_crm_logic():
    # engine = create_engine(DATABASE_URL)
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("--- Testing DB Connectivity ---")
        db.execute(text("SELECT 1"))
        print("DB Connected.")

        print("\n--- Testing Models Existence ---")
        # Try to query empty count for models to ensure tables exist
        print("Customers:", db.query(Customer).count())
        print("Communications:", db.query(Communication).count())
        print("Workspaces:", db.query(Workspace).count())
        # print("AgentSettings:", db.query(AgentSettings).count()) # AgentSettings might be optional

        print("\n--- Testing CRM Service Logic ---")
        # Find a workspace
        workspace = db.query(Workspace).first()
        if not workspace:
            print("No workspace found. Creating mock workspace...")
            # We need a team first
            team = db.query(Team).first()
            if not team:
                print("No team found. Cannot proceed.")
                return
            
            # This part assumes we might need to manually create one if DB is empty
            # But recent signups should have created one.
            pass
        else:
            print(f"Found Workspace: {workspace.id} ({workspace.name})")
            
            service = CRMService(db)
            print("Fetching Stats...")
            stats = service.get_dashboard_stats(workspace.id)
            print("Stats:", stats)

            print("Fetching Activity...")
            activity = service.get_recent_activity(workspace.id)
            print("Activity:", activity)
            
            print("Fetching Customers...")
            customers = service.get_customers(workspace.id)
            print("Customers:", customers)

    except Exception as e:
        import traceback
        print(f"CRASH: {e}")
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    test_crm_logic()
