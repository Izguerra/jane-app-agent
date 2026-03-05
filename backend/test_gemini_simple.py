import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

def test_gemini():
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("Error: No API key found")
        return
        
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    
    for model in models:
        print(f"\n--- Testing Model: {model} ---")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{
                "parts": [{"text": "Hello, are you online?"}]
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Result: Online and working!")
                # print(f"Response: {response.text[:200]}")
            else:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_gemini()
