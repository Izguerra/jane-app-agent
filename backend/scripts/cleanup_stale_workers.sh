#!/bin/zsh

# script to cleanup any stale voice or avatar agent processes
echo "Cleaning up stale agent workers..."

# Find pids for voice_agent.py and avatar_agent.py
PIDS=$(ps aux | grep -E "python.*(voice|avatar)_agent.py" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "Found stale processes: $PIDS"
    echo "$PIDS" | xargs kill -9
    echo "Stale processes terminated."
else
    echo "No stale agent processes found."
fi

# Also remove pid files if they exist
rm -f backend/voice_agent.pid backend/avatar_agent.pid

echo "Cleanup complete."
