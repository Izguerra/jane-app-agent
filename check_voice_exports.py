import livekit.agents.voice as voice
print(dir(voice))
if hasattr(voice, 'VoicePipelineAgent'):
    print("VoicePipelineAgent found!")
if hasattr(voice, 'Agent'):
    print("Agent found!")
