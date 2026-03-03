
import requests
import json
import sys

# Configuration
API_URL = "http://localhost:8000"
AGENT_ID = "agnt_000V7dOUZZ14pBHgCKGRedalkZ6" # From user screenshot
WORKSPACE_ID = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J" # From URL in logs
# Use a specific team_id if known, otherwise we might need to authenticate 
# For this script we'll try to use the headers if we can, 
# but getting a valid token programmatically might be hard without user creds.
# Alternative: Use the python backend code directly.

# APPROACH 2: Direct Backend Call (Bypassing Auth/API for deeper inspection)
# using the exact same logic as `chat.py` but locally.

import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models_db import Agent, Workspace, WorkerTemplate
from backend.agent import AgentManager
from backend.routers.agents import get_agent_settings

def inspect_agent_direct():
    print("--- INSPECTING AGENT IN DB ---")
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.id == AGENT_ID).first()
        if not agent:
            print(f"Agent {AGENT_ID} not found in DB!")
            return
        
        print(f"Agent Name: {agent.name}")
        print(f"Agent Settings: {agent.settings}")
        print(f"Agent Allowed Workers (Column): {agent.allowed_worker_types}")
        
        # Check settings logic
        settings = {}
        if agent.settings: settings.update(agent.settings)
        if agent.allowed_worker_types:
             settings["allowed_worker_types"] = agent.allowed_worker_types
             
        print(f"Computed Settings for Chat: {settings.get('allowed_worker_types')}")
        
        return settings
    finally:
        db.close()

def test_chat_instantiation(settings):
    print("\n--- TESTING AGENT INSTANTIATION ---")
    manager = AgentManager()
    
    # We need to simulate the tools list like in chat.py
    # But for now, let's just see if _create_agent prompts are correct
    
    # Mock parameters
    team_id = 1 # Dummy
    
    # We want to see the system prompt
    # Since _create_agent is internal and returns an Agent object, we can inspect that object.
    
    try:
        # We need to mock the tools dependent on DB? 
        # Actually _create_agent primarily constructs the prompt.
        # But `chat` attaches the tools.
        
        # Let's call `chat` but catch the output
        # `chat` does a lot of DB stuff (calendar tools, etc) which might fail without valid context.
        # So calling _create_agent directly is safer to check the Prompt.
        
        agent_instance = manager._create_agent(settings, team_id, tools=[])
        
        print("\n[System Prompt Instructions]")
        for i, instr in enumerate(agent_instance.instructions):
            print(f"--- Instruction {i} ---")
            print(instr[:200] + "..." if len(instr) > 200 else instr)
            
            if "allowed capabilities" in instr or "ALLOWED capabilities" in instr:
                 print("\n>>> FOUND GATEKEEPER INSTRUCTION <<<")
                 print(instr)
                 
    except Exception as e:
        print(f"Error instantiating agent: {e}")

if __name__ == "__main__":
    settings = inspect_agent_direct()
    if settings:
        test_chat_instantiation(settings)
