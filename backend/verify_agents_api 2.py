import requests
import jwt
import os
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000/agents"
# Use a known secret or fallback
AUTH_SECRET = os.getenv("AUTH_SECRET", "secret_placeholder")
# Use a team ID that we know works or a new one.
# If we used the existing workspace ID earlier, we should use its team_id if possible.
# But creating a new team context is safer for isolation.
MOCK_USER = {
    "user": {
        "id": "verify_user_001",
        "teamId": "REPLACE_ME",
        "email": "verify@test.com",
        "role": "owner"
    }
}

def get_valid_team_id():
    from backend.database import SessionLocal
    from backend.models_db import Team
    db = SessionLocal()
    try:
        team = db.query(Team).first()
        if team:
            return team.id
        else:
             # Create one if none
             print("No team found, creating test team...")
             new_team = Team(id="test_team_001", name="Test Team", plan_name="Starter")
             db.add(new_team)
             db.commit()
             return new_team.id
    except Exception as e:
        print(f"DB Error: {e}")
        return "team_fallback_001"
    finally:
        db.close()

def get_token(team_id):
    user = MOCK_USER.copy()
    user["user"]["teamId"] = team_id
    return jwt.encode(user, AUTH_SECRET, algorithm="HS256")

def run_verification():
    team_id = get_valid_team_id()
    token = get_token(team_id)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print(f"Testing with Token for Team: {MOCK_USER['user']['teamId']}")
    
    # 0. Ensure Workspace Exists (using a NEW team to trigger default creation logic if possible, or just checking existing)
    # Actually, let's use a unique team ID to force default agent creation logic in GET /agents if workspace doesn't exist
    # But get_valid_team_id returns an existing one.
    
    # Let's just check the agent we list/create to see if we can set is_orchestrator or if default has it.
    
    print("\n0. GET /workspaces/me (Ensure Workspace)")
    res = requests.get("http://localhost:8000/workspaces/me", headers=headers)
    if res.status_code == 200:
        print("Success. Workspace ensured.")
    else:
        print(f"Failed to get/create workspace: {res.status_code} - {res.text}")
        return

    # 1. LIST Agents (Should create default workspace/agent if none)
    print("\n1. GET /agents")
    res = requests.get(BASE_URL, headers=headers)
    if res.status_code == 200:
        agents = res.json()
        print(f"Success. Found {len(agents)} agents.")
        print([a['name'] for a in agents])
        print("Success. Found {} agents.".format(len(agents)))
        print(agents)
        
        if len(agents) > 0:
            print(f"Agent 0 is_orchestrator: {agents[0].get('is_orchestrator')}")
    else:
        print(f"Failed: {res.status_code} - {res.text}")
        return

    # 2. CREATE Agent
    print("\n2. POST /agents (Create 'Sales Bot')")
    payload = {
        "name": "Sales Bot",
        "description": "Handles sales inquiries",
        "voice_id": "echo",
        "is_orchestrator": False
    }
    res = requests.post(BASE_URL, headers=headers, json=payload)
    if res.status_code == 200:
        new_agent = res.json()
        agent_id = new_agent['id']
        print(f"Success. Created Agent ID: {agent_id}, Name: {new_agent['name']}")
    else:
        print(f"Failed: {res.status_code} - {res.text}")
        return

    # 3. VERIFY List contains new agent
    print("\n3. GET /agents (Verify List)")
    res = requests.get(BASE_URL, headers=headers)
    agents = res.json()
    found = any(a['id'] == agent_id for a in agents)
    print(f"Agent {agent_id} in list: {found}")

    # 4. FILTER VERIFICATION
    print("\n4. GET /analytics/summary?agent_id=...")
    res = requests.get(f"http://localhost:8000/analytics/summary?agent_id={agent_id}", headers=headers)
    if res.status_code == 200:
        print("Success. Fetched analytics summary with filter.")
        print(res.json())
    else:
        print(f"Failed: {res.status_code} - {res.text}")

    # 5. UPDATE Agent
    print("\n5. PUT /agents/{id} (Update Name)")
    update_payload = {"name": "Super Sales Bot"}
    res = requests.put(f"{BASE_URL}/{agent_id}", headers=headers, json=update_payload)
    if res.status_code == 200:
        updated = res.json()
        print(f"Success. Updated Name: {updated['name']}")
    else:
        print(f"Failed: {res.status_code} - {res.text}")

    # 6. DELETE Agent
    print("\n6. DELETE /agents/{id}")
    res = requests.delete(f"{BASE_URL}/{agent_id}", headers=headers)
    if res.status_code == 200:
        print("Success. Deleted agent.")
    else:
        print(f"Failed: {res.status_code} - {res.text}")

    # 7. VERIFY Delete
    print("\n7. GET /agents (Verify Delete)")
    res = requests.get(BASE_URL, headers=headers)
    agents = res.json()
    found = any(a['id'] == agent_id for a in agents)
    print(f"Agent {agent_id} still in list: {found}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    run_verification()
