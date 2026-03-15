import os
import requests
from dotenv import load_dotenv

load_dotenv("/Users/randyesguerra/Documents/Documents-Randy/Projects/JaneAppAgent/.env")
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")

if not api_key:
    print("API Key not found!")
    exit(1)

models_to_test = [
    "gemini-3.0-flash",
    "gemini-3.0-flash-exp",
    "gemini-3.0-pro",
    "gemini-3.0-pro-exp",
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash"
]

for model in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello"}]}]
    }
    response = requests.post(url, json=payload)
    status = response.status_code
    try:
        msg = response.json().get('error', {}).get('message', 'OK')
    except:
        msg = response.text[:40]
    print(f"Model: {model} -> Status: {status} -> {msg}")
