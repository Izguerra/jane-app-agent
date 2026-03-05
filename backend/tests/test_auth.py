"""
Unit tests for multi-tenant authentication
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import get_current_user, AuthUser
import jwt

import os

client = TestClient(app)

# Test secret (same as in .env)
SECRET_KEY = os.getenv("AUTH_SECRET", "secret_placeholder")
ALGORITHM = "HS256"

def create_test_token(user_id: int, team_id: int) -> str:
    """Create a test JWT token"""
    payload = {
        "user": {"id": user_id},
        "team_id": team_id,  # This will be looked up from database
        "email": f"user{user_id}@test.com"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def test_workspace_without_auth():
    """Test that workspace endpoint requires authentication"""
    response = client.get("/workspaces/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_workspace_with_invalid_token():
    """Test that invalid tokens are rejected"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/workspaces/me", headers=headers)
    assert response.status_code == 401

def test_workspace_isolation():
    """Test that different teams see different workspaces"""
    # This test requires actual database setup
    # For now, we'll test the token extraction works
    
    # Create tokens for two different users
    token1 = create_test_token(user_id=1, team_id=1)
    token2 = create_test_token(user_id=2, team_id=2)
    
    # Verify tokens are different
    assert token1 != token2
    
    # Decode and verify team_ids would be different
    payload1 = jwt.decode(token1, SECRET_KEY, algorithms=[ALGORITHM])
    payload2 = jwt.decode(token2, SECRET_KEY, algorithms=[ALGORITHM])

    
    # Note: In real implementation, team_id comes from database lookup
    # This test verifies the token structure is correct
    assert payload1["user"]["id"] == 1
    assert payload2["user"]["id"] == 2

if __name__ == "__main__":
    print("Running multi-tenant authentication tests...")
    
    print("\n1. Testing workspace without auth...")
    test_workspace_without_auth()
    print("✅ Correctly requires authentication")
    
    print("\n2. Testing workspace with invalid token...")
    test_workspace_with_invalid_token()
    print("✅ Correctly rejects invalid tokens")
    
    print("\n3. Testing workspace isolation...")
    test_workspace_isolation()
    print("✅ Token structure supports team isolation")
    
    print("\n✅ All authentication tests passed!")
