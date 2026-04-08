import requests
import sys

def test_room_validation():
    # Corrected base URL (removed /api prefix)
    base_url = "http://localhost:8000/voice/outbound-twiml"
    
    # Also test the /agent prefix variant
    base_url_agent = "http://localhost:8000/agent/voice/outbound-twiml"
    
    malicious_rooms = [
        "outbound__'_or'='_UHXf768pPRB6",
        "outbound; drop table users--",
        "outbound' OR 1=1 --",
        "room with spaces",
        "room!@#$"
    ]
    
    valid_rooms = [
        "outbound-comm-12345",
        "agent-session-abc-voice",
        "test_room_123"
    ]
    
    for url in [base_url, base_url_agent]:
        print(f"\n=== Testing URL: {url} ===")
        print("--- Testing Malicious Room Names ---")
        for room in malicious_rooms:
            try:
                response = requests.post(f"{url}?room={room}")
                print(f"Room: {room}")
                print(f"Status: {response.status_code}")
                # print(f"Content: {response.text}")
                if "<Dial>" in response.text:
                    print("❌ FAILURE: Malicious room name accepted!")
                else:
                    print("✅ SUCCESS: Malicious room name blocked.")
            except Exception as e:
                print(f"Error testing {room}: {e}")
            print("-" * 20)

        print("\n--- Testing Valid Room Names ---")
        for room in valid_rooms:
            try:
                response = requests.post(f"{url}?room={room}")
                print(f"Room: {room}")
                print(f"Status: {response.status_code}")
                if "<Dial>" in response.text and f"sip:{room}@" in response.text:
                    print("✅ SUCCESS: Valid room name accepted.")
                else:
                    print(f"❌ FAILURE: Valid room name rejected or malformed TwiML. Content: {response.text[:100]}")
            except Exception as e:
                print(f"Error testing {room}: {e}")
            print("-" * 20)

if __name__ == "__main__":
    test_room_validation()
