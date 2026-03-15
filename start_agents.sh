#!/bin/bash
# Path: /Users/randyesguerra/Documents/Documents-Randy/Projects/JaneAppAgent/start_agents.sh
cd "$(dirname "$0")"
source .venv/bin/activate
export PYTHONUNBUFFERED=1

# Kill existing
ps aux | grep -E "voice_agent.py|avatar_agent.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

echo "Starting Voice Agent..."
nohup python backend/voice_agent.py dev </dev/null >> voice_agent_out.log 2>&1 &

echo "Starting Avatar Agent..."
nohup python backend/avatar_agent.py dev </dev/null >> avatar_agent_out.log 2>&1 &

echo "Agents started."
