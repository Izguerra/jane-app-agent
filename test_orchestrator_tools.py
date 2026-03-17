import asyncio
import os
from backend.agents.orchestrator import AgentOrchestrator
from backend.database import SessionLocal
from backend.models_db import Workspace

async def test():
    db = SessionLocal()
    ws = db.query(Workspace).first()
    if not ws:
        print("No workspace found")
        return
    
    workspace_id = ws.id
    team_id = ws.team_id
    
    print(f"Testing orchestrator for workspace: {workspace_id}")
    
    # We don't actually need to call the LLM, just check if tools are extracted
    from backend.agent_tools import AgentTools
    from backend.tools.worker_tools import WorkerTools
    import inspect
    
    worker_tools = WorkerTools(workspace_id=workspace_id)
    agent_tools = AgentTools(workspace_id=workspace_id, worker_tools=worker_tools)
    
    tools = []
    for name, member in inspect.getmembers(agent_tools):
        if type(member).__name__ == "FunctionTool":
            actual_method = getattr(member, "__wrapped__", getattr(member, "_func", None))
            if actual_method and not name.startswith("_"):
                import types
                bound_method = types.MethodType(actual_method, agent_tools)
                tools.append(bound_method)
        elif inspect.ismethod(member) and hasattr(member, "__llm_function__") and not name.startswith("_"):
            tools.append(member)
            
    print(f"Extracted {len(tools)} tools.")
    for t in tools:
        print(f" - {t.__name__}")
        
    db.close()

if __name__ == "__main__":
    asyncio.run(test())
