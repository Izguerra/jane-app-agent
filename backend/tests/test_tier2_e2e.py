import pytest
import os
import jwt
import sys
import types
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, JSON, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1. SETUP ENVIRONMENT AND MOCKS FIRST (BEFORE ANY BACKEND IMPORTS)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LIVEKIT_API_KEY"] = "test_key"
os.environ["LIVEKIT_API_SECRET"] = "test_secret"
os.environ["LIVEKIT_URL"] = "https://test.livekit.cloud"
os.environ["AUTH_SECRET"] = "test_secret"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_123"

# Mock Postgres-specific types for SQLite compatibility
mock_pg = types.ModuleType("postgresql")
mock_pg.JSONB = JSON
mock_pg.ARRAY = lambda x: Text
sys.modules["sqlalchemy.dialects.postgresql"] = mock_pg

# 2. CONFIGURE SHARED TEST DATABASE
import backend.database as db_module
engine = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch the global database module BEFORE other things import from it
db_module.engine = engine
db_module.SessionLocal = TestingSessionLocal

# 3. NOW IMPORT APP AND MODELS
from backend.main import app
from backend.database import Base, get_db, init_db
from backend.models_db import (
    Workspace, Agent, Team, User, TeamMember, 
    Communication, ConversationMessage, Customer
)

# 4. FIX MODULE-LEVEL IMPORTS IN OTHER SERVICES
# Specifically targeting modules that might have imported SessionLocal directly
try:
    import backend.services.conversation_history as ch_service
    ch_service.SessionLocal = TestingSessionLocal
except Exception:
    pass

SECRET_KEY = "test_secret"
ALGORITHM = "HS256"

@pytest.fixture(scope="function")
def db():
    # Ensure all tables are created in the shared engine
    # We call this every time but SQLAlchemy create_all is idempotent
    from backend.models_db import (
        Workspace, Agent, Team, User, TeamMember, 
        Communication, ConversationMessage, Customer
    )
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    
    # Create seed data
    team1 = Team(id="team_1", name="Team One", plan_name="Starter")
    db_ws1 = Workspace(id="ws_1", name="Workspace One", team_id="team_1")
    user1 = User(id="user_1", email="user1@example.com", role="owner", password_hash="dummy")
    tm1 = TeamMember(id="tm_1", user_id="user_1", team_id="team_1", role="owner")
    
    db_agent = Agent(
        id="agent_1", 
        workspace_id="ws_1", 
        name="Test Agent",
        voice_id="alloy",
        language="en",
        is_active=True
    )
    
    session.add_all([team1, db_ws1, user1, tm1, db_agent])
    session.commit()
    
    yield session
    
    # Clean up so next test starts fresh
    session.query(TeamMember).delete()
    session.query(User).delete()
    session.query(Agent).delete()
    session.query(Workspace).delete()
    session.query(Team).delete()
    session.query(Communication).delete()
    session.query(ConversationMessage).delete()
    session.commit()
    session.close()

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

def create_token(user_id: str, team_id: str, role: str = "owner"):
    payload = {
        "user": {
            "id": user_id,
            "teamId": team_id,
            "role": role
        }
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# --- TIER 2 TESTS ---

def test_chat_agent_initialization(client, db):
    """CHAT-1: Verify chat initialization and basic response structure"""
    token = create_token("user_1", "team_1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock the AgentManager.chat method and KnowledgeBaseService
    with patch("backend.agent.AgentManager.chat") as mock_chat, \
         patch("backend.agent.KnowledgeBaseService") as mock_kb:
        
        mock_chat.return_value = "Hello! I am your test agent."
        
        request_data = {
            "message": "Hi there",
            "agent_id": "agent_1",
            "history": []
        }
        
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "content" in data or isinstance(data, str)

def test_voice_token_generation(client, db):
    """VOICE-1: Verify LiveKit token generation for voice agent"""
    token = create_token("user_1", "team_1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock AccessToken and LiveKitAPI from livekit.api
    with patch("livekit.api.AccessToken") as mock_at, \
         patch("livekit.api.LiveKitAPI") as mock_lk_api, \
         patch("backend.agent.KnowledgeBaseService") as mock_kb:
        
        # Setup AccessToken mock
        instance = mock_at.return_value
        instance.with_grants.return_value = instance
        instance.with_identity.return_value = instance
        instance.with_name.return_value = instance
        instance.with_room_config.return_value = instance
        instance.with_metadata.return_value = instance
        instance.to_jwt.return_value = "mock_livekit_jwt"
        
        # Setup LiveKitAPI mock
        mock_lk_instance = mock_lk_api.return_value
        from unittest.mock import AsyncMock
        mock_lk_instance.room = MagicMock()
        mock_lk_instance.room.create_room = AsyncMock()
        mock_lk_instance.aclose = AsyncMock()
        
        request_data = {
            "room_name": "test_room",
            "participant_name": "test_user",
            "agent_id": "agent_1"
        }
        
        response = client.post("/voice/token", json=request_data, headers=headers)
        assert response.status_code == 200
        assert "token" in response.json()
        assert response.json()["token"] == "mock_livekit_jwt"

def test_outbound_twiml_generation(client):
    """VOICE-2: Verify Twilio outbound TwiML generation"""
    response = client.post("/voice/outbound-twiml?room=test_room")
    assert response.status_code == 200
    assert "Response" in response.text
    assert "Sip" in response.text or "Dial" in response.text

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
