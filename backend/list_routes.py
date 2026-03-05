import sys
import os
sys.path.append(os.getcwd())

from backend.main import app

print("Listing all registered routes:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.methods} {route.path}")
