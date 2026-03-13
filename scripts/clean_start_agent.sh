#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}🔪 Hunting down zombie voice agents...${NC}"

# Find all PIDs matching "backend.voice_agent" - refined to avoid killing IDE extensions
PIDS=$(ps aux | grep -v grep | grep -E "python.*backend\.voice_agent" | grep -v "\.antigravity" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No running voice agents found."
else
    echo -e "Found processes: $PIDS"
    # Kill each one with SIGKILL (-9) to ensure they die immediately
    echo "$PIDS" | xargs kill -9
    echo -e "${GREEN}✅ All zombies neutralized.${NC}"
fi

echo -e "${GREEN}🚀 Starting fresh Voice Agent...${NC}"
source .venv/bin/activate
python -m backend.voice_agent dev
