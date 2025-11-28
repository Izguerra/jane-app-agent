import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {url}")
if url:
    print(f"Starts with postgres: {url.startswith('postgres')}")

