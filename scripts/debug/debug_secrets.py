import os
from dotenv import load_dotenv

# Load explicitly from .env file in root
load_dotenv('.env')

secret = os.getenv("AUTH_SECRET")
print(f"PYTHON SECRET: {secret[:5]}..." if secret else "PYTHON SECRET: None")
