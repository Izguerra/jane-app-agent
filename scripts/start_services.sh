#!/bin/bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
export PYTHONUNBUFFERED=1
source .venv/bin/activate
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
nohup npm run dev > frontend.log 2>&1 &
echo $! > frontend.pid
nohup python backend/voice_agent.py dev > voice_agent.log 2>&1 &
echo $! > voice_agent.pid
nohup python backend/avatar_agent.py dev > avatar_agent.log 2>&1 &
echo $! > avatar_agent.pid
echo "All services started."
