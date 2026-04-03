import asyncio
import sys
import os

from dotenv import load_dotenv
load_dotenv(".env")

from livekit.agents.voice import Agent, AgentSession
from livekit.plugins.google.beta.realtime import RealtimeModel

async def main():
    try:
        model = RealtimeModel()
        from livekit.plugins import silero
        agent = Agent(llm=model, vad=silero.VAD.load())
        session = AgentSession()
        print("AgentSession dir:", dir(session))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
