import os
from dotenv import load_dotenv
load_dotenv()

print(f"POSTGRES_URL: {os.getenv('POSTGRES_URL')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

