
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.workspace_service import WorkspaceService
# Mock DB session
from unittest.mock import MagicMock

def verify_service_import():
    print("Verifying WorkspaceService import...")
    try:
        db = MagicMock()
        service = WorkspaceService(db)
        print("✅ WorkspaceService instantiated successfully.")
        
        # Check methods exist
        assert hasattr(service, 'get_workspace_features')
        assert hasattr(service, 'get_workspace_details')
        assert hasattr(service, 'update_workspace_status')
        print("✅ Service methods verified.")
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_service_import()
