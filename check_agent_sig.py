from livekit.agents import llm
from livekit.agents.voice import Agent as VoiceAgent
import inspect

print("ChatContext.add_message signature:", inspect.signature(llm.ChatContext.add_message))
print("VoiceAgent.__init__ signature:", inspect.signature(VoiceAgent.__init__))
