
import sys
import os
import uuid
import time
from datetime import datetime
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.services.worker_provisioner import WorkerProvisioner
from backend.models_db import WorkerInstance, Workspace, Team
from backend.main import app
from backend.auth import get_current_user, AuthUser

def mock_auth_user_owner():
    """Dependency override for Owner"""
    return AuthUser(user_id="owner_user", team_id="team_123", role="owner", email="owner@test.com")

def mock_auth_user_attacker():
    """Dependency override for Attacker (diff team)"""
    return AuthUser(user_id="hacker_user", team_id="team_666", role="member", email="hacker@evil.com")

def mock_auth_user_admin():
    """Dependency override for Admin (diff team but admin role)"""
    return AuthUser(user_id="admin_user", team_id="team_999", role="supaagent_admin", email="admin@supaagent.com")

def test_provisioning_flow():
    print("=== Starting OpenClaw E2E Service Verification ===")
    db = SessionLocal()
    client = TestClient(app)
    
    try:
        # Pre-cleanup trying to find existing team if rerunning locally
        team_id = "team_123"
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            print("Creating dummy team...")
            team = Team(id=team_id, name="Test Team")
            db.add(team)
            db.commit()

        # 1. Setup: Get or Create a Workspace
        # We ensure it has a specific team_id for RBAC testing
        workspace_id = f"wrk_{uuid.uuid4().hex[:8]}"
        workspace = Workspace(
            id=workspace_id, 
            name="Test Workspace", 
            team_id=team_id # Matching our mock owner
        )
        db.add(workspace)
        db.commit()
        
        print(f"Target Workspace: {workspace_id}")
        
        # ==========================================================
        # Part 1: Service Layer (Functionality)
        # ==========================================================
        
        # 2. Test Provisioning (Service Layer)
        print("\n[Step 1] Testing provision_instance() (Service Layer)...")
        provisioner = WorkerProvisioner(db)
        instance = provisioner.provision_instance(
            workspace_id=workspace_id,
            worker_type="openclaw",
            tier="performance",
            name="E2E OpenClaw Bot"
        )
        
        print(f" -> Instance Created: {instance.id}")
        assert instance.status == "active"
        print("✅ Provisioning Successful")

        # ==========================================================
        # Part 2: API Layer (Security/RBAC)
        # ==========================================================
        print("\n[Step 2] Testing API RBAC...")
        
        # 2a. Unauthenticated Access
        print(" -> Testing Unauthenticated Access...")
        app.dependency_overrides = {} # No overrides
        response = client.get(f"/workers/instances?workspace_id={workspace_id}")
        assert response.status_code == 401
        print("   ✅ Passed (401 Unauthorized)")
        
        # 2b. Authorized Access (Owner)
        print(" -> Testing Authorized Access (Owner)...")
        app.dependency_overrides[get_current_user] = mock_auth_user_owner
        response = client.get(f"/workers/instances?workspace_id={workspace_id}")
        assert response.status_code == 200
        instances = response.json()
        assert any(i["id"] == instance.id for i in instances)
        print("   ✅ Passed (200 OK)")
        
        # 2c. Unauthorized Access (Different Team)
        print(" -> Testing Unauthorized Access (Different Team)...")
        app.dependency_overrides[get_current_user] = mock_auth_user_attacker
        response = client.get(f"/workers/instances?workspace_id={workspace_id}")
        assert response.status_code == 403
        print("   ✅ Passed (403 Forbidden)")
        
        # 2d. Authorized Access (Admin / Different Team)
        print(" -> Testing Authorized Access (Admin)...")
        app.dependency_overrides[get_current_user] = mock_auth_user_admin
        response = client.get(f"/workers/instances?workspace_id={workspace_id}")
        assert response.status_code == 200
        instances = response.json()
        assert any(i["id"] == instance.id for i in instances)
        print("   ✅ Passed (200 OK - Admin Override)")
        
        # Reset overrides
        app.dependency_overrides = {}

        # ==========================================================
        # Cleanup
        # ==========================================================

        # 4. Test Termination
        print("\n[Step 3] Cleaning up...")
        success = provisioner.terminate_instance(instance.id)
        assert success
        print("✅ Termination Successful")
        
        print("\n=== E2E Verification Passed! ===")
        
    except AssertionError as e:
        print(f"\n❌ Assertion Failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_provisioning_flow()
