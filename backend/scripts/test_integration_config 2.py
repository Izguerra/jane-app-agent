
import sys
import os
import json
from unittest.mock import MagicMock 

# Add backend to path
sys.path.append(os.getcwd())

from backend.routers.integrations import configure_integration, IntegrationConfig
from backend.models_db import Integration, Workspace
from backend.auth import AuthUser
from fastapi import HTTPException

# Mock dependencies
mock_db = MagicMock()
mock_user = AuthUser(user_id="u1", team_id="t1", role="admin")

# Mock Workspace
mock_workspace = Workspace(id="ws1", team_id="t1")
mock_db.query.return_value.filter.return_value.first.return_value = mock_workspace

# Test Case 1: New Integration, No Credentials
print("\n--- Test 1: New Gmail Integration (Toggle ON) with No Creds ---")

# Mock "Integration not found"
mock_db.query.return_value.filter.return_value.first.side_effect = [mock_workspace, None] 

config = IntegrationConfig(
    provider="gmail_mailbox",
    credentials=None,
    settings={}
)

try:
    # We have to run this in an event loop conceptually, but since we are calling the func directly 
    # and it is async, we need asyncio
    import asyncio
    
    async def run_test():
        try:
            result = await configure_integration("gmail_mailbox", config, mock_user, mock_db)
            print("SUCCESS: Created integration")
            print(result)
        except HTTPException as e:
            print(f"FAILED: {e.status_code} - {e.detail}")
        except Exception as e:
            print(f"ERROR: {e}")

    asyncio.run(run_test())

except Exception as e:
    print(f"Outer Error: {e}")
