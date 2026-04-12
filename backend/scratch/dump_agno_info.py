import inspect
from agno.agent import Agent
from agno.team import Team

def dump_info(cls):
    print(f"--- {cls.__name__} ({cls.__module__}) ---")
    try:
        sig = inspect.signature(cls.__init__)
        print(f"Signature: {sig}")
    except Exception as e:
        print(f"Error getting signature: {e}")
    
    print("Methods:", [m for m in dir(cls) if not m.startswith('_')])
    print("\n")

if __name__ == "__main__":
    dump_info(Agent)
    dump_info(Team)
