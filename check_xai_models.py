
import os
import openai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("XAI_API_KEY")
print(f"Key loaded: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1"
)

try:
    print("Listing models...")
    models = client.models.list()
    for model in models:
        print(f" - {model.id}")
except Exception as e:
    print(f"Error: {e}")
