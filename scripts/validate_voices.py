import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
if not api_key:
    print("Error: ELEVENLABS_API_KEY not found in .env")
    exit(1)

# Hardcoded map from the codebase
VOICE_MAP = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Chris": "iP95p4xoKVk53GoZ742B",
    "Emily": "LcfcDJNUP1GQjkzn1xUU",
    "Josh": "TxGEqnHWrfWFTfGW9XjX",
    "Leo": "IlPhMts77q4KnhTULU2v",
    "Matilda": "XrExE9yKIg1WjnnlVkGX",
    "Nicole": "piTKgcLEGmPE4e6mEKli",
    "Sam": "yoZ06aMxZJJ28mfd3POQ"
}

def validate_voices():
    print(f"Checking voices with API Key: {api_key[:4]}***")
    
    headers = {"xi-api-key": api_key.strip()}
    response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching voices: {response.status_code} - {response.text}")
        return

    all_voices = response.json().get('voices', [])
    voice_lookup = {v['voice_id']: v for v in all_voices}
    name_lookup = {v['name'].lower(): v for v in all_voices}

    print(f"Found {len(all_voices)} voices in your ElevenLabs account.")
    print("-" * 50)
    
    # Print ALL voices for UI update
    print("AVAILABLE VOICES:")
    for v in all_voices:
        print(f" - {v['name']} (Category: {v.get('category')}, ID: {v['voice_id']})")
    print("-" * 50)

    for name, voice_id in VOICE_MAP.items():
        if voice_id in voice_lookup:
            print(f"✅ {name}: Valid ({voice_id})")
        else:
            print(f"❌ {name}: INVALID ID ({voice_id})")
            # Try to find by name
            match = name_lookup.get(name.lower())
            if match:
                print(f"   -> FOUND NEW ID: {match['voice_id']} (Name: {match['name']})")
            else:
                print(f"   -> Voice not found by name either.")

if __name__ == "__main__":
    validate_voices()
