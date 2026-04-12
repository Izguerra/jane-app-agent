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

# 2. Nuclear cleanup of all project-related Python processes
echo "🧹 Killing all zombie and orphan processes..."
pkill -9 -f "uvicorn.*backend.main" || true
pkill -9 -f "python.*voice_agent" || true
pkill -9 -f "python.*avatar_agent" || true
pkill -9 -f "python.*livekit" || true
pkill -9 -f "python.*multimodal" || true
pkill -9 -f "multiprocessing.spawn" || true
pkill -9 -f "multiprocessing.resource_tracker" || true
# Catch any remaining .venv python processes just to be safe
pkill -9 -f ".venv/bin/python" || true

# 3. Remove PID files
rm -f *.pid

echo "🧹 Cleanup complete."
echo "🚀 Restarting services..."

# Start backend in background
nohup .venv/bin/uvicorn backend.main:app --reload --port 8000 > backend.log 2>&1 &
echo "✅ Backend started"

# Wait for backend to be ready
sleep 3

# Start Voice Agent
nohup .venv/bin/python backend/voice_agent.py dev > voice_agent.log 2>&1 &
echo "✅ Voice Agent starting..."

# Start Avatar Agent
nohup .venv/bin/python backend/avatar_agent.py dev > avatar_agent.log 2>&1 &
echo "✅ Avatar Agent starting..."

echo "✨ Hard reset finished. Monitor logs with: tail -f backend.log voice_agent.log"
