import subprocess
import os
import signal
import time
import sys

def kill_process_on_port(port):
    """Finds and kills processes listening on a specific port."""
    try:
        pid = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if pid:
            for p in pid.split("\n"):
                print(f"Killing process {p} on port {port}...")
                os.kill(int(p), signal.SIGKILL)
    except subprocess.CalledProcessError:
        pass

def kill_agents():
    """Kills any running agent processes."""
    patterns = ["voice_agent.py", "avatar_agent.py"]
    for pattern in patterns:
        try:
            subprocess.run(["pkill", "-9", "-f", pattern])
            print(f"Killed all processes matching '{pattern}'")
        except Exception:
            pass

def start_service(command, log_file, name):
    """Starts a service in the background and redirects output to a log file."""
    print(f"Starting {name}...")
    with open(log_file, "w") as f:
        return subprocess.Popen(command, shell=True, stdout=f, stderr=f, preexec_fn=os.setpgrp)

def main():
    print("🚀 Starting JaneApp Dev Stack Restart...")
    
    # 1. Cleanup
    print("🧹 Cleaning up old processes...")
    kill_process_on_port(8000) # Backend
    kill_process_on_port(3000) # Frontend
    kill_agents()
    
    # 2. Wait for sockets to clear
    time.sleep(1)
    
    # 3. Start Services
    # Note: Using absolute paths or ensuring correct CWD
    root = os.getcwd()
    
    # Backend
    start_service("source .venv/bin/activate && uvicorn backend.main:app --port 8000", "backend_restart.log", "Backend")
    
    # Agents
    start_service("source .venv/bin/activate && PYTHONUNBUFFERED=1 python backend/voice_agent.py dev", "voice_agent_restart.log", "Voice Agent")
    start_service("source .venv/bin/activate && PYTHONUNBUFFERED=1 python backend/avatar_agent.py dev", "avatar_agent_restart.log", "Avatar Agent")
    
    # Frontend
    start_service("npm run dev", "frontend_restart.log", "Frontend")
    
    print("\n✅ Restart initiated!")
    print("Check logs for details:")
    print("- Backend: backend_restart.log")
    print("- Voice: voice_agent_restart.log")
    print("- Avatar: avatar_agent_restart.log")
    print("- Frontend: frontend_restart.log")
    print("\nFrontend should be ready at http://localhost:3000 in ~10 seconds.")

if __name__ == "__main__":
    main()
