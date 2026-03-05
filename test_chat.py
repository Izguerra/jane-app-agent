import asyncio
from backend.agent import AgentManager
from backend.database import SessionLocal

async def test():
    db = SessionLocal()
    mgr = AgentManager()
    agent_id = "agnt_000VCRoP3S1834dms8YCdys6m8P"
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    team_id = "team_1"
    
    stream = await mgr.chat(
        message="who won the world series baseball in 2025?",
        team_id=team_id,
        workspace_id=workspace_id,
        agent_id=agent_id,
        db=db,
        communication_id="test_comm_1",
        stream=True
    )
    async for chunk in stream:
        print(chunk.content if hasattr(chunk, 'content') else chunk, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(test())
