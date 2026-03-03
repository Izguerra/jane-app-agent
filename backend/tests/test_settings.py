import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base
from backend.models_db import Agent, Workspace
from backend.settings_store import get_settings, save_settings
from backend.agent import AgentManager
import os
import jwt


# Setup in-memory SQLite database for testing
# Use StaticPool to maintain the same connection for in-memory DB across threads
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test settings
ALGORITHM = "HS256"
DEV_TEAM_ID = "org_000V7dMzThAVrPNF3XBlRXq4MO"

@pytest.fixture(scope="function")

def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_session_local(db_session):
    """Mock the SessionLocal in settings_store to use our test session."""
    with patch("backend.settings_store.SessionLocal", return_value=db_session):
        yield db_session

def test_get_settings_creates_defaults(mock_session_local):
    """Test that get_settings creates default clinic and settings if they don't exist."""
    settings = get_settings(workspace_id="ws_1")

    
    assert settings["voice_id"] == "alloy"
    assert settings["language"] == "en"
    assert settings["is_active"] is True
    
    # Verify records were created in DB
    workspace = mock_session_local.query(Workspace).filter_by(id="ws_1").first()
    assert workspace is not None
    assert workspace.name == "Demo Workspace"
    
    db_settings = mock_session_local.query(Agent).filter_by(workspace_id="ws_1").first()

    assert db_settings is not None
    assert db_settings.voice_id == "alloy"

def test_save_settings_updates_db(mock_session_local):
    """Test that save_settings updates the existing record."""
    # First ensure defaults exist
    get_settings(workspace_id="ws_1")

    
    new_config = {
        "voice_id": "echo",
        "language": "es",
        "is_active": False,
        "prompt_template": "New prompt"
    }
    
    save_settings(new_config, workspace_id="ws_1")

    
    # Verify update
    db_settings = mock_session_local.query(Agent).filter_by(workspace_id="ws_1").first()

    assert db_settings.voice_id == "echo"
    assert db_settings.language == "es"
    assert db_settings.is_active is False
    assert db_settings.prompt_template == "New prompt"

def test_get_settings_retrieves_updated(mock_session_local):
    """Test that get_settings returns the updated values."""
    # Setup initial state
    get_settings(workspace_id="ws_1")
    save_settings({"voice_id": "shimmer"}, workspace_id="ws_1")
    
    # Retrieve
    settings = get_settings(workspace_id="ws_1")

    assert settings["voice_id"] == "shimmer"

def test_agent_manager_creates_dynamic_agent(mock_session_local):
    """Test that AgentManager creates an agent with the correct settings."""
    # Setup custom settings
    custom_prompt = "You are a custom agent."
    save_settings({"language": "fr", "prompt_template": custom_prompt}, workspace_id="ws_1")

    
    # Patch get_settings in agent.py to return our test settings
    with patch("backend.agent.get_settings") as mock_get_settings:
        mock_get_settings.return_value = {
            "voice_id": "alloy",
            "language": "fr",
            "prompt_template": custom_prompt,
            "is_active": True
        }
        
        manager = AgentManager()
        # We access the private method just to verify agent creation logic
        # Signature: _create_agent(self, settings: dict, workspace_id: str, team_id: str, ...)
        agent = manager._create_agent(
            mock_get_settings.return_value, 
            workspace_id="ws_1", 
            team_id="org_1"
        )

        
        # Check instructions include custom prompt and language
        assert any(custom_prompt in instr for instr in agent.instructions)
        # AgentManager maps "fr" to "French"
        assert any("respond in French" in instr for instr in agent.instructions)


from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

@pytest.fixture
def client(db_session):
    """Test client with mocked DB session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(mock_session_local):
    """Provide authentication headers for tests."""
    # Ensure workspace exists and matches the DEV_TEAM_ID bypass
    ws = mock_session_local.query(Workspace).filter_by(id="ws_1").first()
    if ws:
        ws.team_id = DEV_TEAM_ID
        mock_session_local.add(ws)
        mock_session_local.commit()
    else:
        ws = Workspace(id="ws_1", team_id=DEV_TEAM_ID, name="Demo Workspace")
        mock_session_local.add(ws)
        mock_session_local.commit()
        
    return {"Authorization": "Bearer DEVELOPER_BYPASS", "x-workspace-id": "ws_1"}

def test_api_get_settings(client, auth_headers):
    # Ensure an agent exists so get_settings works if it expects one
    get_settings(workspace_id="ws_1")
    # The global /settings endpoint returns workspace info, not agent settings

    response = client.get("/settings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "ws_1"

def test_api_get_options(client, auth_headers):
    # Options are now under /agents/options
    response = client.get("/agents/options", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert "languages" in data
    assert len(data["voices"]) > 0
    assert len(data["languages"]) > 0

def test_api_agents_list(client, auth_headers):
    # Ensure an agent exists
    get_settings(workspace_id="ws_1")
    # Verify we can list agents
    response = client.get("/agents", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["workspace_id"] == "ws_1"

