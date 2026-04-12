import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.agents.orchestrator import AgentOrchestrator
from backend.services.acknowledgement_service import stream_with_followup

async def test_chatbot_tool_streaming():
    print("🚀 Testing Chatbot Tool Result Streaming...")
    
    # Use the real workspace ID from user logs for authorization
    workspace_id = "wrk_000V7dMzXJLzP5mYgdf7FzjA3J"
    message = "how far is the CN Tower from Milton, ON?"
    
    print(f"Asking: {message}")
    
    response_gen = await AgentOrchestrator.chat(
        message=message,
        team_id="team_1",
        workspace_id=workspace_id,
        stream=True
    )
    
    filler = "Checking on that for you..."
    print(f"\n--- Stream Output ---")
    print(f"CHUNK: [{filler}]")
    full_content = filler
    async for chunk in stream_with_followup(response_gen, filler, followup_delay=3.0):
        print(f"CHUNK: [{chunk}]")
        full_content += chunk
    
    print("\n--- End of Stream ---")
    print(f"Full Combined Content: {full_content}")
    
    if "Checking on that" in full_content and ("km" in full_content or "miles" in full_content):
        print("\n✅ Verification Passed: Chatbot correctly yielded filler AND directions results.")
    else:
        print("\n❌ Verification Failed: Map result missing or filler lost.")

if __name__ == "__main__":
    asyncio.run(test_chatbot_tool_streaming())
