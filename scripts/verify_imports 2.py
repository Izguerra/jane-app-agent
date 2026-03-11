
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

print("Verifying imports...")

separator = "=" * 40
print(separator)

modules_to_check = [
    "backend.routers.campaigns",
    "backend.routers.voice",
    "backend.routers.agents",
    "backend.routers.admin_settings",
    "backend.routers.workspaces",
    "backend.routers.billing",
]

for module in modules_to_check:
    print(f"Importing {module}...", end=" ")
    try:
        __import__(module)
        print("OK")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

print(separator)
print("All imports verified successfully.")
