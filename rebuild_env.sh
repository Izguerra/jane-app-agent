#!/bin/bash

echo "=============================================="
echo "    CLEANING UP ALL ZOMBIE PROCESSES          "
echo "=============================================="

# Kill exact python matches to avoid killing Antigravity or VS Code
pkill -9 -f "python backend/voice_agent.py" || true
pkill -9 -f "python backend/avatar_agent.py" || true
pkill -9 -f "uvicorn" || true

# Kill frontend matches
pkill -9 -f "next-dev" || true
pkill -9 -f "npm run dev" || true

echo "Waiting for ports to be freed..."
sleep 2

echo "=============================================="
echo "    STARTING DEVELOPMENT ENVIRONMENT          "
echo "=============================================="

# Ensure we are in the right directory
cd /Users/randyesguerra/Documents/Documents-Randy/Projects/JaneAppAgent

# 1. Start Backend API
echo "Starting Backend API (uvicorn)..."
source .venv/bin/activate
nohup uvicorn backend.main:app --reload --port 8000 > backend_server.log 2>&1 &

# Wait briefly for backend to initialize
sleep 2

# 2. Start Voice Agent
echo "Starting Voice Agent v2.1..."
nohup python backend/voice_agent.py dev >> voice_agent.log 2>&1 &

# 3. Start Avatar Agent
echo "Starting Avatar Agent v2.1..."
nohup python backend/avatar_agent.py dev >> avatar_agent.log 2>&1 &

# 4. Start Frontend
echo "Starting Frontend (Next.js)..."
nohup npm run dev >> frontend_server.log 2>&1 &

echo "=============================================="
echo "    REBUILD COMPLETE & SERVERS RUNNING        "
echo "=============================================="
echo "You can check the logs in:"
echo "- backend_server.log"
echo "- voice_agent.log"
echo "- avatar_agent.log"
echo "- frontend_server.log"
