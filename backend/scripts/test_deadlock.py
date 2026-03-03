
import asyncio
import functools
import nest_asyncio
import aiohttp

# Apply nest_asyncio globally like main.py does
nest_asyncio.apply()

# Mock External Tools
class MockExternalTools:
    async def get_current_weather(self, location: str):
        print(f"    [Tool] Fetching weather for {location}...")
        async with aiohttp.ClientSession() as session:
            # We use a real URL or google to ensure network I/O happens
            async with session.get("http://www.google.com") as resp:
                print(f"    [Tool] Network call done. Status: {resp.status}")
        return f"Weather in {location} is Sunny"

# Mock Worker Logic (Synchronous wrapper around async tool)
def execute_worker_logic(location):
    print(f"  [Worker] Executing logic for {location} in thread...")
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        print("  [Worker] Found running loop? (Should not happen in thread)")
        result = loop.run_until_complete(MockExternalTools().get_current_weather(location))
    except RuntimeError:
        print("  [Worker] No running loop in thread. Using asyncio.run()...")
        result = asyncio.run(MockExternalTools().get_current_weather(location))
    except Exception as e:
        print(f"  [Worker] Error: {e}")
        return str(e)
        
    print(f"  [Worker] Result: {result}")
    return result

# Mock WorkerTools (Async dispatch)
async def run_task_now(location):
    print(f"[Main] run_task_now called for {location}")
    loop = asyncio.get_running_loop()
    
    handler_func = functools.partial(execute_worker_logic, location)
    
    print("[Main] Offloading to executor...")
    result = await loop.run_in_executor(None, handler_func)
    print(f"[Main] Success! Result: {result}")

async def main():
    print("--- STARTING DEADLOCK TEST ---")
    try:
        # Run with timeout to detect hang
        await asyncio.wait_for(run_task_now("TestCity"), timeout=10.0)
    except asyncio.TimeoutError:
        print("\n❌❌ DEADLOCK DETECTED: Operation timed out! ❌❌")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    print("--- END TEST ---")

if __name__ == "__main__":
    asyncio.run(main())
