import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base
from backend.models_db import AgentSettings, Clinic
from backend.settings_store import get_settings, save_settings
from backend.agent import AgentManager

# Setup in-memory SQLite database for testing
# Use StaticPool to maintain the same connection for in-memory DB across threads
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    settings = get_settings(clinic_id=1)
    
    assert settings["voice_id"] == "alloy"
    assert settings["language"] == "en"
    assert settings["is_active"] is True
    
    # Verify records were created in DB
    clinic = mock_session_local.query(Clinic).filter_by(id=1).first()
    assert clinic is not None
    assert clinic.name == "Demo Clinic"
    
    db_settings = mock_session_local.query(AgentSettings).filter_by(clinic_id=1).first()
    assert db_settings is not None
    assert db_settings.voice_id == "alloy"

def test_save_settings_updates_db(mock_session_local):
    """Test that save_settings updates the existing record."""
    # First ensure defaults exist
    get_settings(clinic_id=1)
    
    new_config = {
        "voice_id": "echo",
        "language": "es",
        "is_active": False,
        "prompt_template": "New prompt"
    }
    
    save_settings(new_config, clinic_id=1)
    
    # Verify update
    db_settings = mock_session_local.query(AgentSettings).filter_by(clinic_id=1).first()
    assert db_settings.voice_id == "echo"
    assert db_settings.language == "es"
    assert db_settings.is_active is False
    assert db_settings.prompt_template == "New prompt"

def test_get_settings_retrieves_updated(mock_session_local):
    """Test that get_settings returns the updated values."""
    # Setup initial state
    get_settings(clinic_id=1)
    save_settings({"voice_id": "shimmer"}, clinic_id=1)
    
    # Retrieve
    settings = get_settings(clinic_id=1)
    assert settings["voice_id"] == "shimmer"

def test_agent_manager_creates_dynamic_agent(mock_session_local):
    """Test that AgentManager creates an agent with the correct settings."""
    # Setup custom settings
    custom_prompt = "You are a custom agent."
    save_settings({"language": "fr", "prompt_template": custom_prompt}, clinic_id=1)
    
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
        agent = manager._create_agent(mock_get_settings.return_value)
        
        # Check instructions include custom prompt and language
        assert any(custom_prompt in instr for instr in agent.instructions)
        assert any("respond in fr" in instr for instr in agent.instructions)

from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client(mock_session_local):
    """Test client with mocked DB session."""
    return TestClient(app)

def test_api_get_settings(client):
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["voice_id"] == "alloy"

def test_api_update_settings(client):
    payload = {
        "voice_id": "nova",
        "language": "de",
        "is_active": True
    }
    response = client.put("/settings", json=payload)
    assert response.status_code == 200
    
    # Verify persistence via GET
    response = client.get("/settings")
    data = response.json()
    assert data["voice_id"] == "nova"
    assert data["language"] == "de"

def test_api_get_options(client):
    response = client.get("/settings/options")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert "languages" in data
    assert len(data["voices"]) > 0
    assert len(data["languages"]) > 0
