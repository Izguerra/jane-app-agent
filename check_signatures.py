from livekit.api.egress_service import EgressService
from livekit.agents.llm import LLM
import inspect

print("--- EgressService.__init__ ---")
print(inspect.signature(EgressService.__init__))

print("\n--- EgressService MRO ---")
print(EgressService.mro())

try:
    from livekit.agents import VoicePipelineAgent
    print("\n--- VoicePipelineAgent Events ---")
    # It's hard to list events dynamically, but we can check if 'on' exists and maybe docstrings
    print(dir(VoicePipelineAgent))
except ImportError:
    pass
