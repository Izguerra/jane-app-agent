#!/bin/bash

# Kill existing services
echo "Stopping existing services..."
# Frontend usually on 3000
PORT_3000=$(lsof -t -i:3000)
if [ ! -z "$PORT_3000" ]; then
    echo "Killing process on port 3000 (PID: $PORT_3000)"
    kill -9 $PORT_3000
fi

# Backend usually on 8000
PORT_8000=$(lsof -t -i:8000)
if [ ! -z "$PORT_8000" ]; then
    echo "Killing process on port 8000 (PID: $PORT_8000)"
    kill -9 $PORT_8000
fi

# Voice/Avatar agents - refined to avoid killing IDE extensions (like Pyre)
PIDS=$(ps aux | grep -v grep | grep -E "python.*(voice_agent|avatar_agent)" | grep -v "\.antigravity" | awk '{print $2}')
if [ ! -z "$PIDS" ]; then
    echo "Killing agent processes: $PIDS"
    kill -9 $PIDS
fi

# Start Database
echo "Starting Database..."
docker compose up -d

# Environment Setup
export PYTHONPATH=.
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Start Backend
echo "Starting Backend on port 8000..."
./.venv/bin/python3 -m uvicorn backend.main:app --port 8000 --host 0.0.0.0 >> backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start Voice Agent
echo "Starting Voice Agent..."
export AGENT_NAME="supaagent-voice-v2.1"
nohup ./.venv/bin/python3 -m backend.voice_agent dev >> voice_agent.log 2>&1 &
VOICE_PID=$!
echo "Voice Agent PID: $VOICE_PID"

# Start Avatar Agent
echo "Starting Avatar Agent..."
export AGENT_NAME="supaagent-avatar-v2.1"
nohup ./.venv/bin/python3 -m backend.avatar_agent dev >> avatar_agent.log 2>&1 &
AVATAR_PID=$!
echo "Avatar Agent PID: $AVATAR_PID"

# Start Frontend
echo "Starting Frontend on port 3000..."
npm run dev >> frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo "All services have been triggered to start."
echo "Check backend.log, voice_agent.log, avatar_agent.log, and frontend.log for status."
