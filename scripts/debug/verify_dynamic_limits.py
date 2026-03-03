import sys
import os
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.services.subscription_service import SubscriptionService
from backend.models_db import SubscriptionUsage, Workspace, Team
from backend.subscription_limits import PLAN_LIMITS
from backend.lib.id_service import IdService
from datetime import datetime

def verify_dynamic_limits():
    db = SessionLocal()
    workspace_id = "verify_test_workspace"
    team_id = "verify_test_team"
    
    try:
        # 0. Setup: Create a dummy Team and Workspace
        
        # Check team
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            team = Team(
                id=team_id,
                name="Verify Test Team",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(team)
            db.commit()

        # Check workspace 
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            ws = Workspace(
                id=workspace_id,
                name="Verify Test Workspace",
                team_id=team_id, # Link to team
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(ws)
            db.commit()

        service = SubscriptionService(db)
        
        # 1. Ensure subscription exists (will be starter by default)
        service.get_subscription(workspace_id)
        
        # 2. Get Usage (creates it)
        usage = service.get_usage(workspace_id)
        original_limit = usage.voice_minutes_limit
        print(f"Initial Limit: {original_limit}")
        
        # 3. Simulate a "stale" limit by manually modifying the DB record
        # Let's pretend the limit used to be 10, but the plan says it should be 75 (or whatever PLAN_LIMITS says)
        usage.voice_minutes_limit = 10.0
        db.commit()
        db.refresh(usage)
        print(f"Modified Limit (Simulated Stale): {usage.voice_minutes_limit}")
        
        assert usage.voice_minutes_limit == 10.0, "Failed to simulate stale limit"
        
        # 4. Call get_usage again - THIS SHOULD TRIGGER THE SYNC
        updated_usage = service.get_usage(workspace_id)
        print(f"Refetched Limit: {updated_usage.voice_minutes_limit}")
        
        # 5. Assert it snapped back to the Plan Limit
        expected_limit = PLAN_LIMITS["starter"]["voice_minutes"]
        
        if updated_usage.voice_minutes_limit == expected_limit:
            print(f"SUCCESS: Limit synced dynamically to {expected_limit}")
        else:
            print(f"FAILURE: Limit {updated_usage.voice_minutes_limit} != Expected {expected_limit}")
            exit(1)
            
    finally:
        # Cleanup
        try:
            db.query(SubscriptionUsage).filter(SubscriptionUsage.workspace_id == workspace_id).delete()
            from backend.models_db import Subscription
            db.query(Subscription).filter(Subscription.workspace_id == workspace_id).delete()
            db.query(Workspace).filter(Workspace.id == workspace_id).delete()
            db.query(Team).filter(Team.id == team_id).delete()
            db.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")
        db.close()

if __name__ == "__main__":
    verify_dynamic_limits()
