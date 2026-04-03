import asyncio
import os
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins.google.realtime import RealtimeModel
from livekit.agents import llm

# Mock function to add a tool
def my_tool():
    pass

async def main():
    model = RealtimeModel()
    
    # In livekit-agents 1.5.1, ToolContext requires tools in the initializer in some versions / we can just use an empty list or ignore it
    fnc_ctx = llm.ToolContext() if hasattr(llm.ToolContext, "default") else None
    
    agent = Agent(llm=model, instructions="Hello", tools=[])
    print(f"Agent instantiated: {agent}")
    
    print("Success.")

if __name__ == '__main__':
    asyncio.run(main())
