
from backend.services.brain_service import BrainService

class MockSkill:
    def __init__(self, slug):
        self.slug = slug

skills = [MockSkill("email-worker"), MockSkill("weather-worker"), MockSkill("lead-research")]
allowed = BrainService.get_allowed_tool_names(skills)

print(f"Allowed Methods: {allowed}")
if "run_task_now" in allowed and "get_weather" in allowed and "send_email_notification" in allowed:
    print("✅ Tool Extraction SUCCESS")
else:
    print("❌ Tool Extraction FAILED")
