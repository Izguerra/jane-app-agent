
import subprocess
import time
import os
import signal

def start_and_wait():
    VENV_PYTHON = "/Users/randyesguerra/Documents/Documents-Randy/Projects/JaneAppAgent/.venv/bin/python"
    LOG_FILE = "voice_agent.log"
    
    # Kill any existing
    subprocess.run(["pkill", "-f", "voice_agent.py"])
    time.sleep(2)
    
    print(">>> Starting Voice Agent...")
    with open(LOG_FILE, "w") as f:
        proc = subprocess.Popen(
            [VENV_PYTHON, "backend/voice_agent.py", "start"],
            stdout=f,
            stderr=f,
            preexec_fn=os.setpgrp # detach from terminal
        )
    
    # Wait for "registered worker"
    start_time = time.time()
    timeout = 20
    registered = False
    
    while time.time() - start_time < timeout:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.read()
                if "registered worker" in content:
                    print("✅ Worker Registered Successfully!")
                    registered = True
                    break
        time.sleep(1)
        
    if not registered:
        print("❌ Worker failed to register within timeout.")
        # Print last few lines of log
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                print("Last log lines:")
                print(f.readlines()[-10:])

if __name__ == "__main__":
    start_and_wait()
