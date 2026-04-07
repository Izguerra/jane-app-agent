from livekit.agents.voice import AgentSession
import inspect

print("AgentSession.start signature:")
try:
    print(inspect.signature(AgentSession.start))
except Exception as e:
    print(f"Error: {e}")
