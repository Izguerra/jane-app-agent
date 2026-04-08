import inspect
from livekit.agents import llm

class MyTools:
    @llm.function_tool(description="test")
    def my_fnc(self):
        pass
        
t = MyTools()
for name, member in inspect.getmembers(t):
    if type(member).__name__ == "FunctionTool":
        print(f"Found FunctionTool: {name}")
        print(f"Has _fnc: {hasattr(member, '_fnc')}")
        print(f"Has fnc: {hasattr(member, 'fnc')}")
        print(dir(member))
