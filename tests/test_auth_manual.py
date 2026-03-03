import pytest
from fastapi import Request, HTTPException
from unittest.mock import MagicMock, patch
from backend.auth import get_current_user, AuthUser
from backend.routers.auth import google_callback
import os

# Mock environment variables
os.environ["AUTH_SECRET"] = "test_secret"
os.environ["GOOGLE_CLIENT_ID"] = "test_client_id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test_client_secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/api/auth/google/callback"

@pytest.mark.asyncio
async def test_get_current_user_manual_call():
    """
    Test that get_current_user can be called manually with just the request object
    and authorization=None, relying on cookies.
    """
    # Mock request with session cookie
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"session": "valid_token"}
    mock_request.headers = {}

    # Mock jwt.decode
    with patch("jose.jwt.decode") as mock_jwt_decode:
        mock_jwt_decode.return_value = {
            "user": {"id": 1, "teamId": 1},
            "email": "test@example.com"
        }
        
        # Call get_current_user manually as done in google_callback
        user = await get_current_user(mock_request, authorization=None)
        
        assert isinstance(user, AuthUser)
        assert user.id == 1
        assert user.team_id == 1
        assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_manual_call_no_token():
    """
    Test that get_current_user raises HTTPException when no token is present.
    """
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {}
    mock_request.headers = {}

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(mock_request, authorization=None)
    
    assert excinfo.value.status_code == 401

