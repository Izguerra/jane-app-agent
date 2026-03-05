#!/bin/bash

# Kill existing processes
echo "Stopping existing services..."

# Kill Next.js (Port 3000)
PID_3000=$(lsof -ti:3000)
if [ ! -z "$PID_3000" ]; then
    echo "Killing process on port 3000 (PID: $PID_3000)"
    kill -9 $PID_3000
fi

# Kill FastAPI (Port 8000)
PID_8000=$(lsof -ti:8000)
if [ ! -z "$PID_8000" ]; then
    echo "Killing process on port 8000 (PID: $PID_8000)"
    kill -9 $PID_8000
fi

# Kill Voice Agent
PIDS_AGENT=$(pgrep -f "backend.voice_agent")
if [ ! -z "$PIDS_AGENT" ]; then
    echo "Killing voice agent processes: $PIDS_AGENT"
    echo "$PIDS_AGENT" | xargs kill -9
fi

# Start Docker
echo "Starting Database..."
docker-compose up -d

# Check for virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found!"
    exit 1
fi

# Start Backend
echo "Starting Backend on port 8000..."
nohup uvicorn backend.main:app --reload --port 8000 > backend.log 2>&1 &
echo "Backend PID: $!"

# Start Voice Agent
echo "Starting Voice Agent..."
nohup python -m backend.voice_agent dev > voice_agent.log 2>&1 &
echo "Voice Agent PID: $!"

# Start Frontend
echo "Starting Frontend on port 3000..."
nohup npm run dev > frontend.log 2>&1 &
echo "Frontend PID: $!"

echo "All services have been triggered to start."
echo "Check backend.log, voice_agent.log, and frontend.log for status."
