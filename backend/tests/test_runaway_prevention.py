import requests
import os
import time
import subprocess
import threading
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def get_agent_process_count():
    try:
        # Count processes for both voice and avatar agents
        output = subprocess.check_output(["pgrep", "-f", "voice_agent.py\|avatar_agent.py"]).decode().strip()
        return len(output.split("\n")) if output else 0
    except subprocess.CalledProcessError:
        return 0

def test_malformed_room_rejection_with_process_audit():
    print("\n--- Testing Malformed Room Rejection (Process Audit) ---")
    initial_count = get_agent_process_count()
    print(f"Initial agent processes: {initial_count}")
    
    malformed_room = "outbound--_'or'='_AuditTest"
    url = f"{BACKEND_URL}/voice/outbound-twiml?room={malformed_room}"
    
    print(f"Sending malformed request to {url}")
    try:
        response = requests.post(url)
        print(f"Status: {response.status_code}")
        print(f"Content: {response.text}")
        
        # Expect 403 Forbidden and Reject TwiML
        assert response.status_code == 403
        assert "Reject" in response.text
        
        # Give LiveKit/Worker a moment to potentially spawn a process if it was going to
        print("Waiting 3s for any potential background spawns...")
        time.sleep(3)
        
        final_count = get_agent_process_count()
        print(f"Final agent processes: {final_count}")
        
        if final_count <= initial_count:
            print("✅ PASS: No new agent processes spawned for malformed room.")
        else:
            print(f"❌ FAIL: {final_count - initial_count} new processes spawned and still running!")
            
    except Exception as e:
        print(f"Error: {e}")

def test_chaos_probe_wave():
    print("\n--- Testing Chaos Probe Wave (10 simultaneous probes) ---")
    initial_count = get_agent_process_count()
    print(f"Initial agent processes: {initial_count}")
    
    threads = []
    def send_probe(i):
        room = f"outbound--_'or'='_Chaos_{i}"
        try:
            requests.post(f"{BACKEND_URL}/voice/outbound-twiml?room={room}", timeout=5)
        except Exception:
            pass

    print("Launching 10 simultaneous probes...")
    for i in range(10):
        t = threading.Thread(target=send_probe, args=(i,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
        
    print("Wave sent. Waiting for potential worker spikes...")
    time.sleep(5)
    
    final_count = get_agent_process_count()
    print(f"Final agent processes after wave: {final_count}")
    
    if final_count <= initial_count:
        print("✅ PASS: System remained stable under probe wave. No runaways.")
    else:
        print(f"❌ FAIL: System leaked {final_count - initial_count} processes during wave!")

def test_legitimate_room_resolution():
    print("\n--- Testing Legitimate Room Resolution ---")
    valid_room = "outbound-comm-v1-abcdef123456"
    url = f"{BACKEND_URL}/voice/outbound-twiml?room={valid_room}"
    
    print(f"Requesting (POST): {url}")
    try:
        response = requests.post(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200 and "Dial" in response.text:
            print("✅ PASS: Legitimate room pattern accepted.")
        else:
            print("❌ FAIL: Legitimate room pattern was blocked or returned invalid TwiML.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        # Ensure we are testing against a running server
        requests.get(BACKEND_URL)
        
        test_malformed_room_rejection_with_process_audit()
        test_chaos_probe_wave()
        test_legitimate_room_resolution()
    except requests.exceptions.ConnectionError:
        print(f"❌ FAIL: Backend not running at {BACKEND_URL}")
    except Exception as e:
        print(f"Test failed: {e}")
