import asyncio
import os
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins.google.realtime import RealtimeModel
from livekit.agents import llm
from livekit import rtc

async def main():
    model = RealtimeModel()
    agent = Agent(llm=model, instructions="", tools=[])
    session = AgentSession()
    
    # We mock a room here just to see if type checks pass
    room = rtc.Room()
    
    try:
        # Don't await it to avoid actually trying to connect without keys
        task = asyncio.create_task(session.start(agent=agent, room=room))
        print("AgentSession start task created successfully!")
        task.cancel()
    except Exception as e:
        print(f"Error starting: {e}")

if __name__ == '__main__':
    asyncio.run(main())
