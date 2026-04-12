import os
import glob

def replace_in_file(filepath, old_text, new_text):
    with open(filepath, 'r') as file:
        filedata = file.read()
    
    if old_text in filedata:
        filedata = filedata.replace(old_text, new_text)
        with open(filepath, 'w') as file:
            file.write(filedata)
        print(f"Updated {filepath}")

# Target files from grep results
files = [
    "backend/services/brain_service.py",
    "backend/scripts/verify_unification_e2e.py",
    "backend/scripts/multimodal_backend_shakedown.py",
    "backend/scripts/test_tool_regex.py",
    "backend/scripts/validate_skill_toggle_e2e.py",
    "backend/voice_agent.py",
    "backend/avatar_agent.py",
    "backend/agents/factory.py",
    "backend/agents/orchestrator.py"
]

for f in files:
    if os.path.exists(f):
        replace_in_file(f, "voice_prompt_builder", "brain_service")
        replace_in_file(f, "VoicePromptBuilder", "BrainService")
    else:
        print(f"File not found: {f}")
print("Mass rename complete.")
