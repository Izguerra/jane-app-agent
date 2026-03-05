import sys
import os

# Set up path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

try:
    print("Testing avatar_agent imports...")
    from backend import avatar_agent
    print("Avatar Agent imported.")
except Exception as e:
    print(f"FAILED to import avatar_agent: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting voice_agent imports...")
    from backend import voice_agent
    print("Voice Agent imported.")
except Exception as e:
    print(f"FAILED to import voice_agent: {e}")
    import traceback
    traceback.print_exc()

print("\nImport test complete.")
