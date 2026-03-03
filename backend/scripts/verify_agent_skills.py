import sys
import os
from unittest.mock import MagicMock

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- MOCKING MISSING MODULES ---
import types

# Mock agno
agno = types.ModuleType("agno")
agno.agent = types.ModuleType("agno.agent")
class MockAgent:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
agno.agent.Agent = MockAgent
sys.modules["agno"] = agno
sys.modules["agno.agent"] = agno.agent

# Mock other potential missing deps
sys.modules["pinecone"] = MagicMock()
sys.modules["livekit"] = MagicMock()
sys.modules["livekit.agents"] = MagicMock()
sys.modules["livekit.agents.llm"] = MagicMock()

from backend.agent import AgentManager

def verify_agent_skills():
    print("=== Starting Agent Skills Verification ===")
    
    # 1. Setup Mock Data
    settings = {
        "business_name": "Test Clinic",
        "prompt_template": "You are a friendly health assistant.",
        "allowed_worker_types": ["sms-messaging"]
    }
    
    workspace_id = "test_wrk_123"
    team_id = "test_team_456"
    
    # Mock Skills
    mock_skill_1 = MagicMock()
    mock_skill_1.name = "CRM Manager"
    mock_skill_1.slug = "crm-worker"
    mock_skill_1.instructions = "Manage customer records with empathy."
    
    mock_skill_2 = MagicMock()
    mock_skill_2.name = "Appointment Scheduler"
    mock_skill_2.slug = "calendar-worker"
    mock_skill_2.instructions = "Book appointments using availability rules."
    
    enabled_skills = [mock_skill_1, mock_skill_2]
    
    # Mock Personality
    personality_prompt = "TONE: Professional and calm. SPIRIT: Helpful healer."
    
    # 2. Instantiate AgentManager
    am = AgentManager()
    
    # 3. Call _create_agent
    print("Testing _create_agent with skills and personality...")
    agent = am._create_agent(
        settings=settings,
        workspace_id=workspace_id,
        team_id=team_id,
        enabled_skills=enabled_skills,
        personality_prompt=personality_prompt
    )
    
    # 4. Verify Instructions
    instructions = agent.instructions
    full_prompt = "\n".join(instructions)
    
    print("\n--- GENERATED PROMPT PREVIEW ---")
    print(full_prompt[:500] + "...")
    print("--- END PREVIEW ---\n")
    
    # Assertions
    print("Running Checks:")
    
    checks = {
        "Personality injection": personality_prompt in instructions[0],
        "Standard prompt template": settings["prompt_template"] in full_prompt,
        "Skill 1 name": mock_skill_1.name in full_prompt,
        "Skill 1 instructions": mock_skill_1.instructions in full_prompt,
        "Skill 2 name": mock_skill_2.name in full_prompt,
        "Skill 2 instructions": mock_skill_2.instructions in full_prompt,
        "Allowed workers merging": "crm-worker" in full_prompt and "calendar-worker" in full_prompt and "sms-messaging" in full_prompt
    }
    
    all_passed = True
    for name, passed in checks.items():
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {name}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\n✅ Verification Successful: AgentManager correctly injects skills and personality.")
    else:
        print("\n❌ Verification Failed: One or more checks did not pass.")
        sys.exit(1)

if __name__ == "__main__":
    verify_agent_skills()
