#!/bin/bash
# Hard reset script for JaneApp Agent environment

echo "🛑 Stopping all services..."

# 1. Kill any process on backend and agent ports
for port in 8000 8081 8082; do
    pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        echo "Killing processes on port $port (PIDs: $pid)"
        kill -9 $pid
    fi
done

# 2. Kill any generic uvicorn or python agent processes
pkill -f "uvicorn backend.main:app" || true
pkill -f "python backend/voice_agent.py" || true
pkill -f "python backend/avatar_agent.py" || true

# 3. Remove PID files
rm -f *.pid

echo "🧹 Cleanup complete."
echo "🚀 Restarting services..."

# Start backend in background
nohup .venv/bin/uvicorn backend.main:app --reload --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
echo "✅ Backend started (PID $(cat backend.pid))"

# Wait for backend to be ready
sleep 3

# Start Voice Agent
nohup .venv/bin/python backend/voice_agent.py dev > voice_agent.log 2>&1 &
echo $! > voice_agent.pid
echo "✅ Voice Agent started (PID $(cat voice_agent.pid))"

# Start Avatar Agent
nohup .venv/bin/python backend/avatar_agent.py dev > avatar_agent.log 2>&1 &
echo $! > avatar_agent.pid
echo "✅ Avatar Agent started (PID $(cat avatar_agent.pid))"

echo "✨ Hard reset finished. Monitor logs with: tail -f backend.log voice_agent.log"
