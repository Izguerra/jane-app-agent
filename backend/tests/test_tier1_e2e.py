import pytest
import os
import jwt
import sys
import types
from unittest.mock import MagicMock

# Force SQLite for database.py before it loads
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import Column, String, JSON, Text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Mock Postgres-specific types for SQLite compatibility
mock_pg = types.ModuleType("postgresql")
mock_pg.JSONB = JSON
mock_pg.ARRAY = lambda x: Text
sys.modules["sqlalchemy.dialects.postgresql"] = mock_pg

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, get_db
from backend.models_db import Workspace, Agent, Team
from backend.lib.id_service import IdService

# Setup in-memory SQLite for E2E Tier 1 tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use same secret as in tests/test_auth.py fallback or env
SECRET_KEY = os.getenv("AUTH_SECRET", "secret_placeholder")
ALGORITHM = "HS256"

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Create seed data for isolation testing
    team1 = Team(id="team_1", name="Team One")
    team2 = Team(id="team_2", name="Team Two")
    db_ws1 = Workspace(id="ws_1", name="Workspace One", team_id="team_1")
    db_ws2 = Workspace(id="ws_2", name="Workspace Two", team_id="team_2")
    
    session.add_all([team1, team2, db_ws1, db_ws2])
    session.commit()
    
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def create_token(user_id: str, team_id: str, role: str = "admin"):
    payload = {
        "user": {
            "id": user_id,
            "teamId": team_id,
            "role": role
        }
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def test_health_check(client):
    """Verify core API is alive"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_unauthorized(client):
    """Verify protected endpoints require auth"""
    response = client.get("/workspaces")
    assert response.status_code == 401

def test_workspace_isolation(client, db):
    """WS-1 & AUTH-2: Verify users only see their own workspaces via /me"""
    # Create tokens for different teams with owner role for /me access
    token1 = create_token("user_1", "team_1", role="owner")
    token2 = create_token("user_2", "team_2", role="owner")
    
    # Team 1 user should see WS 1 info via /workspaces/me
    headers1 = {"Authorization": f"Bearer {token1}"}
    response1 = client.get("/workspaces/me", headers=headers1)
    assert response1.status_code == 200
    assert response1.json()["name"] == "Workspace One"

    # Team 2 user should see WS 2 info via /workspaces/me
    headers2 = {"Authorization": f"Bearer {token2}"}
    response2 = client.get("/workspaces/me", headers=headers2)
    assert response2.status_code == 200
    assert response2.json()["name"] == "Workspace Two"

    # Verify that a non-admin (member) cannot access the global admin list
    member_token = create_token("user_3", "team_1", role="member")
    headers_member = {"Authorization": f"Bearer {member_token}"}
    response_admin_fail = client.get("/workspaces", headers=headers_member)
    assert response_admin_fail.status_code == 403

def test_page_routing_simulation(client):
    """Test simulated endpoint routing representing Next.js pages"""
    token = create_token("user_1", "team_1")
    headers = {"Authorization": f"Bearer {token}"}
    
    routes = [
        "/workspaces",
        "/agents",
        "/crm/stats",
        "/appointments",
        "/skills"
    ]
    
    for route in routes:
        response = client.get(route, headers=headers)
        # We don't check for 200 exactly if it requires params, but 404 means route is missing
        assert response.status_code != 404, f"Route {route} not found"
        print(f"Verified route: {route} -> {response.status_code}")

if __name__ == "__main__":
    pytest.main([__file__])
