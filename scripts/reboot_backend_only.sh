#!/bin/bash

# Kill existing processes
echo "Stopping Backend and Voice Agent services..."

# Kill FastAPI (Port 8000)
PID_8000=$(lsof -ti:8000)
if [ ! -z "$PID_8000" ]; then
    echo "Killing Backend on port 8000 (PID: $PID_8000)"
    kill -9 $PID_8000
fi

# Kill Voice Agent - refined to avoid killing IDE extensions (like Pyre)
PIDS_AGENT=$(ps aux | grep -v grep | grep -E "python.*backend\.voice_agent" | grep -v "\.antigravity" | awk '{print $2}')
if [ ! -z "$PIDS_AGENT" ]; then
    echo "Killing Voice Agent processes: $PIDS_AGENT"
    echo "$PIDS_AGENT" | xargs kill -9
fi

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

echo "Backend and Voice Agent have been restarted."
echo "Check backend.log and voice_agent.log for status."
