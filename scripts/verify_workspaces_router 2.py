
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock key dependencies BEFORE importing the router
# This prevents ImportError if some services try to connect to real external services on import
sys.modules['backend.services.crm_analytics_service'] = MagicMock()
sys.modules['backend.services.workspace_service'] = MagicMock()

# Now import router
from backend.routers.workspaces import get_all_workspaces, get_workspace, update_workspace_status, WorkspaceStatusUpdate
from backend.models_db import Workspace, Team, User, Agent, PhoneNumber
from backend.auth import AuthUser

def verify_router_endpoints():
    print("Verifying Workspaces Router logic...")
    
    # Mock Objects
    db = MagicMock()
    current_user = AuthUser(
        user_id="user_123", 
        email="admin@test.com", 
        role="supaagent_admin", 
        team_id="team_123"
    )
    
    # --- Test 1: get_all_workspaces ---
    print("Testing 'get_all_workspaces'...")
    try:
        # Mock DB data
        mock_ws = Workspace(id="ws_1", team_id="team_1", name="Test WS", created_at=datetime.utcnow())
        db.query.return_value.all.return_value = [mock_ws]
        
        # Mock secondary queries inside the loop
        db.query.return_value.filter.return_value.first.return_value = Team(id="team_1", plan_name="Starter", subscription_status="active")
        # Mock owner query
        mock_row = MagicMock()
        mock_row.email = "owner@test.com"
        mock_row.first_name = "John"
        mock_row.last_name = "Doe"
        db.execute.return_value.fetchone.return_value = mock_row
        
        # Mock CRM Service behavior
        # We need to mock the IMPORT inside the function if it does local import
        with patch('backend.services.crm_analytics_service.CRMAnalyticsService') as MockCRM:
            mock_crm_instance = MockCRM.return_value
            mock_crm_instance.get_workspace_usage_stats.return_value = {
                "voice_minutes_used": 100,
                "conversations_count": 50
            }
            
            response = get_all_workspaces(db=db, current_user=current_user)
            
            assert response["total"] == 1
            assert response["items"][0]["name"] == "Test WS"
            assert response["items"][0]["monthly_calls"] == 100
            print("✅ 'get_all_workspaces' passed.")
            
    except Exception as e:
        print(f"❌ 'get_all_workspaces' failed: {e}")
        import traceback
        traceback.print_exc()

    # --- Test 2: update_workspace_status ---
    print("Testing 'update_workspace_status'...")
    try:
        # Access the Mock we already injected
        MockServiceClass = sys.modules['backend.services.workspace_service'].WorkspaceService
        mock_instance = MockServiceClass.return_value
        # Configure return value
        mock_instance.update_workspace_status.return_value = {
            "success": True, 
            "status": "suspended"
        }
        
        update_data = WorkspaceStatusUpdate(status="suspended")
        result = update_workspace_status("ws_1", update_data, db=db, current_user=current_user)
        
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["status"] == "suspended"
        print("✅ 'update_workspace_status' passed.")
            
    except Exception as e:
        print(f"❌ 'update_workspace_status' failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_router_endpoints()
