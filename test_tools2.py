from livekit.agents import llm
import inspect
class MyTools:
    @llm.function_tool(description="test")
    def my_fnc(self, arg1: str):
        return f"Called my_fnc with {arg1}"

t = MyTools()
for name, member in inspect.getmembers(t):
    if type(member).__name__ == "FunctionTool":
        fnc = getattr(member, "_func", getattr(member, "__wrapped__", None))
        try:
            print("Trying to call unwrapped without self...")
            res = fnc("test")
            print(res)
        except Exception as e:
            print(f"Failed: {e}")
            
        try:
            print("Trying to call bound method...")
            # We can bind it back!
            import types
            bound_method = types.MethodType(fnc, t)
            res = bound_method("test")
            print(res)
        except Exception as e:
            print(f"Failed to bind: {e}")
