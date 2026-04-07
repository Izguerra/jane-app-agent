from livekit.agents.voice import AgentSession, Agent
import inspect

print("AgentSession methods:")
for name, member in inspect.getmembers(AgentSession):
    if not name.startswith('_'):
        print(f" - {name}")

print("\nAgent methods (aliased as VoiceAgent in bridge):")
for name, member in inspect.getmembers(Agent):
    if not name.startswith('_'):
        print(f" - {name}")
