import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.agents.orchestrator import AgentOrchestrator
from backend.services.acknowledgement_service import stream_with_followup

async def test_chatbot_tool_streaming():
    print("🚀 Testing Chatbot Tool Result Streaming...")
    
    # We'll use a real query that triggers a tool (Weather)
    # Use a dummy workspace with the weather key from ENV
    workspace_id = "wrk_local_shakedown"
    message = "what is the temperature in Tokyo right now?"
    
    print(f"Asking: {message}")
    
    response_gen = await AgentOrchestrator.chat(
        message=message,
        team_id="team_1",
        workspace_id=workspace_id,
        stream=True
    )
    
    print("\n--- Stream Output ---")
    full_content = ""
    async for chunk in stream_with_followup(response_gen, "Checking that now...", followup_delay=3.0):
        print(f"CHUNK: [{chunk}]")
        full_content += chunk
    
    print("\n--- End of Stream ---")
    print(f"Full Combined Content: {full_content}")
    
    if "Checking that now" in full_content and "Tokyo" in full_content and "°" in full_content:
        print("\n✅ Verification Passed: Chatbot correctly yielded filler AND tool results.")
    else:
        print("\n❌ Verification Failed: Final result missing from stream.")

if __name__ == "__main__":
    asyncio.run(test_chatbot_tool_streaming())
