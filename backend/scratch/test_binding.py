import asyncio
import inspect
from livekit.agents import llm

class Mixin:
    @llm.function_tool(description="Test tool")
    async def test_tool(self, arg1: str):
        return f"Success: {arg1} (self type: {type(self)})"

class AgentTools(Mixin):
    def __init__(self):
        pass

async def main():
    agent_tools = AgentTools()
    lk_tools = llm.find_function_tools(agent_tools)
    
    for tool_obj in lk_tools:
        tool_name = tool_obj.info.name
        actual_func = getattr(tool_obj, "_func", None)
        
        print(f"Tool: {tool_name}")
        print(f"Is method (actual_func): {inspect.ismethod(actual_func)}")
        
        # This is the logic I implemented in orchestrator:
        async def wrapper(*args, **kwargs):
            if inspect.ismethod(actual_func):
                print("Calling as BOUND method")
                return await actual_func(*args, **kwargs)
            else:
                print("Calling as UNBOUND function")
                raw_func = getattr(actual_func, "__wrapped__", actual_func)
                return await raw_func(agent_tools, *args, **kwargs)

        result = await wrapper(arg1="Hello world")
        print(f"Result: {result}")
        
        # Test original failing logic (passing self to bound method)
        print("\nTesting original failing scenario (should raise TypeError if bound)...")
        try:
            raw_func = getattr(actual_func, "__wrapped__", actual_func)
            await raw_func(agent_tools, arg1="This will fail if bound")
            print("Status: FAILED (Didn't raise TypeError, logic might have been complex)")
        except TypeError as e:
            print(f"Status: PASSED (Correctly raised TypeError: {e})")

if __name__ == "__main__":
    asyncio.run(main())
