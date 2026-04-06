import asyncio
from livekit.agents.voice import AgentSession
from livekit.agents.llm import ChatContext
class MockLLM:
    def session(self):
        class MockSession:
            pass
        return MockSession()
async def main():
    sess = AgentSession(llm=MockLLM(), vad=None, stt=None, tts=None)
    print("AgentSession attrs:")
    for a in dir(sess):
        if not a.startswith("__"): print(a)
asyncio.run(main())
