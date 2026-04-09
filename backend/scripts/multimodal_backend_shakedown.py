import sys
import os
import asyncio
from datetime import datetime
import pytz

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.voice_prompt_builder import VoicePromptBuilder
from backend.services.skill_service import SkillService
from backend.agents.factory import AgentFactory
from backend.tools.external_tools import ExternalTools

class MockSkill:
    def __init__(self, name, slug, instructions):
        self.name = name
        self.slug = slug
        self.instructions = instructions

class MockParticipant:
    def __init__(self, metadata):
        self.metadata = metadata
        self.attributes = {}

class MockRoom:
    def __init__(self, metadata, name):
        self.metadata = metadata
        self.name = name

class MockContext:
    def __init__(self, metadata, name):
        self.room = MockRoom(metadata=metadata, name=name)

async def run_shakedown():
    print("🚀 Starting Multimodal Backend Shakedown...\n")
    
    # ── Phase 1: Identity & Context Resolution ──
    print("--- Phase 1: Identity & Context Resolution ---")
    from backend.services.voice_context_resolver import VoiceContextResolver
    import json
    
    # Simulate an Avatar connecting with workspace metadata
    mock_meta = json.dumps({"workspace_id": "wrk_123456", "agent_id": "ag_123456"})
    ctx = MockContext(metadata=mock_meta, name="avatar_room")
    participant = MockParticipant(metadata=mock_meta)
    
    ws_id, ag_id, call_ctx, settings = await VoiceContextResolver.resolve_context(ctx, participant)
    
    assert ws_id == "wrk_123456", f"Failed to resolve workspace! Got: {ws_id}"
    assert ag_id == "ag_123456", f"Failed to resolve agent! Got: {ag_id}"
    print("✅ Identity Resolution Passed (Mock LiveKit Context Extracted)\n")

    # ── Phase 2: Skill Access Parity ──
    print("--- Phase 2: Skill Access Parity ---")
    enabled_skills = [
        MockSkill("Flight Tracker", "flight-tracker", "Track flights via FlightAware"),
        MockSkill("Weather Lookup", "weather-worker", "Ask about the sky.")
    ]
    
    allowed_methods = VoicePromptBuilder.get_allowed_tool_names(enabled_skills)
    assert "get_flight_status" in allowed_methods, "Flight tracker not authorized by One-Brain!"
    assert "run_task_now" in allowed_methods, "Worker router not authorized!"
    print(f"✅ Skill Access Parity Passed. Allowed Methods: {allowed_methods}\n")

    # ── Phase 3: Prompt Generation Parity ──
    print("--- Phase 3: Prompt Generation Parity ---")
    settings = {
        "agent_type": "personal",
        "client_timezone": "America/Toronto",
        "business_name": "SupaAgent Test",
        "soul": "You are helpful."
    }
    workspace_info = {"name": "SupaAgent Test", "role": "Personal Assistant"}
    
    ref_tz = pytz.timezone(settings["client_timezone"])
    voice_time = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
    
    voice_prompt = VoicePromptBuilder.build_prompt(
        settings, "Be concise", enabled_skills, workspace_info,
        voice_time, "Toronto, CA", agent_type="personal"
    )
    
    chatbot_agent = AgentFactory.create_agent(
        settings=settings, workspace_id="wrk_123", team_id="team_1",
        enabled_skills=enabled_skills, personality_prompt="Be concise", current_datetime=voice_time
    )
    
    assert "YOUR REFERENCE TIME:" in voice_prompt, "Voice missing core rules."
    assert "YOUR REFERENCE TIME:" in chatbot_agent.instructions, "Chatbot missing core rules."
    assert "get_flight_status" in voice_prompt, "Voice missing flight tool."
    assert "get_flight_status" in chatbot_agent.instructions, "Chatbot missing flight tool."
    assert "4 1 6 -" in voice_prompt, "Voice missing pronunciation rules."
    print("✅ Prompt Unification Passed (Identical Rules Generated)\n")

    # ── Phase 4: Aero API Integration (Real API Call) ──
    print("--- Phase 4: FlightAware Aero API Functional Test ---")
    
    # Test tracking by Flight Number
    tools = ExternalTools(workspace_id=ws_id)
    res_ident = await tools.get_flight_status(flight_number="AC100")
    
    assert "FlightAware" not in res_ident, f"Expected data, got configuration error: {res_ident}"
    assert "Status: " in res_ident, f"Failed to parse Aero API payload: {res_ident}"
    print(f"✅ Single Flight lookup Passed\n{res_ident}\n")
    
    # Test tracking by Route Schedule
    res_route = await tools.get_flight_status(origin="CYYZ", destination="KJFK")
    assert "Error:" not in res_route, f"Crash detected in route search: {res_route}"
    assert "Status: " in res_route, "Failed to parse schedule payload."
    print(f"✅ Route Schedule lookup Passed. Found flights between CYYZ and KJFK.\n")

    print("✨ ALL END-TO-END MULTIMODAL SHAKEDOWN TESTS PASSED SUCCESSFULLY! ✨")

if __name__ == "__main__":
    try:
        asyncio.run(run_shakedown())
    except AssertionError as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)
