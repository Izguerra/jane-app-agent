
import sys
import os

sys.path.append(os.getcwd())

from backend.database import Base, engine
# Import ALL models to ensure registration
from backend.models_db import * 

if __name__ == "__main__":
    print("Inspect Base.metadata.tables keys:")
    for key in Base.metadata.tables.keys():
        print(f" - {key}")
        
    # Force create again
    print("Running create_all again...")
    Base.metadata.create_all(bind=engine)
    print("Done.")
