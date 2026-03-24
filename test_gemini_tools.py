import asyncio
from livekit.agents import llm
from livekit.plugins import google
from backend.agent_tools import AgentTools
from dotenv import load_dotenv
load_dotenv()

async def test():
    tools = AgentTools(workspace_id="test")
    all_tools = llm.find_function_tools(tools)
    
    from backend.services.integration_service import IntegrationService
    from backend.database import SessionLocal
    from backend.models_db import Workspace
    
    db = SessionLocal()
    ws = db.query(Workspace).first()
    db.close()
    
    key = None
    if ws:
        key = IntegrationService.get_provider_key(ws.id, "openai", "OPENAI_API_KEY")
    
    if not key:
        print("No openai key found!")
        return
        
    from livekit.plugins import openai
    model = openai.LLM(model="gpt-4o-mini", api_key=key)
    print(f"Loaded {len(all_tools)} tools.")
    
    msg = llm.ChatMessage(content="What's the weather in New York?", role="user")
    chat_ctx = llm.ChatContext(messages=[msg])
    try:
        print("Calling chat...")
        stream = await model.chat(chat_ctx=chat_ctx, fnc_ctx=all_tools)
        async for chunk in stream:
            pass
        print("Success!")
    except Exception as e:
        print(f"Gemini Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
