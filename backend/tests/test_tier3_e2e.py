
import pytest
import os
import jwt
import sys
import types
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy import create_engine, JSON, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1. SETUP ENVIRONMENT AND MOCKS (SQLITE COMPATIBILITY)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AUTH_SECRET"] = "test_secret"
os.environ["OPENAI_API_KEY"] = "test_openai_key"

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
db_module.engine = engine
db_module.SessionLocal = TestingSessionLocal

# 3. IMPORT MODELS AND APP
from backend.database import Base
from backend.models_db import (
    Workspace, Agent, Team, User, TeamMember, 
    WorkerTask, WorkerTemplate
)
from backend.agent import AgentManager

SECRET_KEY = "test_secret"
ALGORITHM = "HS256"

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed data
    team1 = Team(id="team_3", name="Tier 3 Team", plan_name="Pro")
    ws1 = Workspace(id="ws_3", name="Tier 3 Workspace", team_id="team_3")
    user1 = User(id="user_3", email="tier3@example.com", role="owner", password_hash="dummy")
    tm1 = TeamMember(id="tm_3", user_id="user_3", team_id="team_3", role="owner")
    
    # Create test agent
    agent1 = Agent(
        id="agent_3", 
        workspace_id="ws_3", 
        name="Tool Agent",
        is_active=True,
        allowed_worker_types=["weather-worker"] # Limited for SKILL-1 test
    )
    
    # Create a worker record
    weather_worker = WorkerTemplate(
        id="weather_w",
        slug="weather-worker",
        name="Weather Worker",
        is_active=True
    )
    
    session.add_all([team1, ws1, user1, tm1, agent1, weather_worker])
    session.commit()
    
    yield session
    
    # Explicitly clear tables
    for model in [WorkerTask, WorkerTemplate, Agent, TeamMember, User, Workspace, Team]:
        session.query(model).delete()
    session.commit()
    session.close()

def create_token(user_id: str, team_id: str):
    payload = {"user": {"id": user_id, "teamId": team_id, "role": "owner"}}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# --- TIER 3 TESTS ---

@pytest.mark.asyncio
async def test_run_task_now_success(db):
    """TOOL-1: Verify sync worker execution logic via AgentManager"""
    manager = AgentManager()
    
    # We want to test the implementation of 'run_task_now' tool defined in AgentManager.chat
    # Since it's a nested function, we'll mock the 'agno.Agent' and capture the tools
    
    with patch("backend.agent.Agent") as MockAgnoAgent, \
         patch("backend.agent.KnowledgeBaseService"), \
         patch("backend.agent_tools.get_worker_handler") as mock_handler_finder:
        
        # Proper async mock for Agent instance
        mock_agent_instance = MockAgnoAgent.return_value
        mock_response = MagicMock()
        mock_response.content = "Mock response"
        mock_agent_instance.arun = AsyncMock(return_value=mock_response)
        
        # Mock worker handler returning a string
        mock_handler = MagicMock()
        mock_handler.return_value = "The weather is sunny."
        mock_handler_finder.return_value = mock_handler
        
        # Instantiate the manager and start a chat (which creates the agno agent)
        # We don't care about the final response, we just want to extract the tool
        await manager.chat(
            message="What is the weather in London?",
            agent_id="agent_3",
            workspace_id="ws_3",
            team_id="team_3",
            stream=False
        )
        
        # Extract the 'run_task_now' function passed to the Agno Agent
        # MockAgnoAgent.call_args.kwargs['tools'] contains the list of functions
        found_tools = MockAgnoAgent.call_args.kwargs.get('tools', [])
        run_task_now_fn = next((f for f in found_tools if f.__name__ == "run_task_now"), None)
        
        assert run_task_now_fn is not None, "run_task_now tool not found in agent tools"
        
        # Now call the actual tool function logic!
        result = await run_task_now_fn(worker_type="weather-worker", parameters={"location": "London"})
        
        assert "The weather is sunny" in result
        
        # Verify DB record
        task = db.query(WorkerTask).filter(WorkerTask.worker_type == "weather-worker").first()
        assert task is not None
        assert task.status == "completed"
        assert task.output_data == "The weather is sunny."

@pytest.mark.asyncio
async def test_dispatch_worker_task_success(db):
    """TOOL-2: Verify async worker dispatch logic"""
    manager = AgentManager()
    
    with patch("backend.agent.Agent") as MockAgnoAgent, \
         patch("backend.agent.KnowledgeBaseService"):
        
        # Proper async mock for Agent instance
        mock_agent_instance = MockAgnoAgent.return_value
        mock_response = MagicMock()
        mock_response.content = "Mock response"
        mock_agent_instance.arun = AsyncMock(return_value=mock_response)
        
        await manager.chat(
            message="Start a background job search",
            agent_id="agent_3",
            workspace_id="ws_3",
            team_id="team_3",
            stream=False
        )
        
        found_tools = MockAgnoAgent.call_args.kwargs.get('tools', [])
        dispatch_fn = next((f for f in found_tools if f.__name__ == "dispatch_worker_task"), None)
        
        assert dispatch_fn is not None
        
        # Dispatch unauthorized worker (job-search is NOT in allowed_worker_types for agent_3)
        result = await dispatch_fn(worker_type="job-search", parameters={"query": "python"})
        assert "Error: Unauthorized" in result
        
        # Dispatch authorized worker (weather-worker)
        result = await dispatch_fn(worker_type="weather-worker", parameters={"location": "NYC"})
        assert "Task dispatched. ID:" in result
        
        # Verify DB record
        task = db.query(WorkerTask).filter(WorkerTask.worker_type == "weather-worker").first()
        assert task is not None
        assert task.status == "pending"

@pytest.mark.asyncio
async def test_skill_authorization_enforcement(db):
    """SKILL-1: Verify permission blocks"""
    manager = AgentManager()
    
    with patch("backend.agent.Agent") as MockAgnoAgent, \
         patch("backend.agent.KnowledgeBaseService"):
        
        # Proper async mock for Agent instance
        mock_agent_instance = MockAgnoAgent.return_value
        mock_response = MagicMock()
        mock_response.content = "Mock response"
        mock_agent_instance.arun = AsyncMock(return_value=mock_response)
        
        await manager.chat(
            message="Do something unauthorized",
            agent_id="agent_3",
            workspace_id="ws_3",
            team_id="team_3",
            stream=False
        )
        
        found_tools = MockAgnoAgent.call_args.kwargs.get('tools', [])
        run_task_now_fn = next((f for f in found_tools if f.__name__ == "run_task_now"), None)
        
        # agent_3 only allows "weather-worker"
        result = await run_task_now_fn(worker_type="forbidden-worker", parameters={})
        assert "Error: You are not authorized" in result

if __name__ == "__main__":
    pytest.main([__file__])
