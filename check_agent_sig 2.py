from livekit.agents.voice import Agent, AgentSession
import inspect

print("Agent signature:", inspect.signature(Agent.__init__))
print("AgentSession signature:", inspect.signature(AgentSession.__init__))
print("AgentSession.start signature:", inspect.signature(AgentSession.start))
