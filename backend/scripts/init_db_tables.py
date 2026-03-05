
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import init_db

if __name__ == "__main__":
    print("Initializing database tables...")
    init_db()
    print("Done.")
