import os

# Centralized Port Management for AI Agents
# Prevents OSError: [Errno 48] address already in use
AVATAR_AGENT_PORT = int(os.getenv("AVATAR_AGENT_PORT", "8081"))
VOICE_AGENT_PORT = int(os.getenv("VOICE_AGENT_PORT", "8082"))
CHAT_AGENT_PORT = int(os.getenv("CHAT_AGENT_PORT", "8083"))

# Other shared settings
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
