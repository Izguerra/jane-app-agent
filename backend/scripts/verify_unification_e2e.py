import sys
import os
from datetime import datetime
import pytz

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.voice_prompt_builder import VoicePromptBuilder
from backend.services.skill_service import SkillService
from backend.services.personality_service import PersonalityService
from backend.agents.factory import AgentFactory

class MockSkill:
    def __init__(self, name, slug, instructions):
        self.name = name
        self.slug = slug
        self.instructions = instructions

def verify_unification():
    print("🚀 Starting One Brain Unification E2E Verification...\n")
    
    # ── Test Data ──
    settings = {
        "agent_type": "personal",
        "client_timezone": "America/Toronto",
        "business_name": "Randy's Lab",
        "soul": "You are helpful and precise.",
        "allowed_worker_types": ["sms-messaging"]
    }
    
    workspace_info = {
        "name": "Randy's Lab",
        "role": "Personal Assistant",
        "services": "General Support",
        "phone": "+1234567890"
    }

    personality_prompt = "Speak with a friendly, tech-savvy tone."
    
    # Enable specific skills
    enabled_skills = [
        MockSkill("Web Research", "web-research", "Use web_search for news."),
        MockSkill("Weather Lookup", "weather-worker", "Ask about the sky.")
    ]

    # ── 1. Simulate Voice Agent Prompt Generation ──
    print("--- Testing Voice Agent Prompt ---")
    ref_tz = pytz.timezone(settings["client_timezone"])
    voice_time = datetime.now(ref_tz).strftime("%A, %B %d, %Y at %I:%M %p")
    
    voice_prompt = VoicePromptBuilder.build_prompt(
        settings, personality_prompt, enabled_skills, workspace_info,
        voice_time, "Toronto, CA", agent_type="personal"
    )
    
    # Assertions
    assert "YOUR REFERENCE TIME:" in voice_prompt, "Voice prompt missing reference time label"
    assert "web_search" in voice_prompt, "Voice prompt missing enabled direct tool (web_search)"
    assert "get_weather" in voice_prompt, "Voice prompt missing enabled direct tool (get_weather)"
    assert "America/Toronto" in voice_prompt, "Voice prompt missing correct timezone reference"
    print("✅ Voice Agent Prompt Verified (Unified & Dynamic)\n")

    # ── 2. Simulate Avatar Agent Prompt Generation ──
    print("--- Testing Avatar Agent Prompt ---")
    # Avatar handles metadata for call_context
    avatar_prompt = VoicePromptBuilder.build_prompt(
        settings, personality_prompt, enabled_skills, workspace_info,
        voice_time, "Toronto, CA", agent_type="personal",
        call_context={"intent": "Follow up on research"}
    )
    
    assert "MISSION-CRITICAL CALL CONTEXT" in avatar_prompt, "Avatar prompt missing mission context"
    assert "web_search" in avatar_prompt, "Avatar prompt missing enabled direct tool"
    print("✅ Avatar Agent Prompt Verified (Unified & Dynamic)\n")

    # ── 3. Simulate Chatbot (AgentFactory) Prompt Generation ──
    print("--- Testing Chatbot (AgentFactory) Prompt ---")
    chatbot_agent = AgentFactory.create_agent(
        settings=settings,
        workspace_id="ws_123",
        team_id="team_123",
        enabled_skills=enabled_skills,
        personality_prompt=personality_prompt,
        current_datetime=voice_time
    )
    
    chatbot_instructions = chatbot_agent.instructions
    
    assert "YOUR REFERENCE TIME:" in chatbot_instructions, "Chatbot instructions missing unified reference time"
    assert "web_search" in chatbot_instructions, "Chatbot instructions missing enabled direct tool"
    assert "IMMEDIATE DYNAMIC ACKNOWLEDGMENT" in chatbot_instructions, "Chatbot missing unified conversational rules"
    print("✅ Chatbot (AgentFactory) Prompt Verified (Unified & Dynamic)\n")

    print("✨ E2E VERIFICATION SUCCESSFUL: All agents are correctly using the unified VoicePromptBuilder brain.")

if __name__ == "__main__":
    try:
        verify_unification()
    except AssertionError as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)
