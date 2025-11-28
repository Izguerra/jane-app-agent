from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_agent_settings():
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "voice_id" in data
    assert "language" in data
    assert data["voice_id"] == "alloy"

def test_get_integrations():
    response = client.get("/integrations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_chat_endpoint_mock():
    # This might fail if it tries to hit real OpenAI, but let's see if it handles auth/mocking
    # If it fails, we know we need to mock the agent_manager
    pass
