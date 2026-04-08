#!/bin/bash
# Start MCP Servers required for JaneApp Agent

# Load environment variables
source .env

# 1. Playwright Browser MCP (Port 8931 as defined in DB)
echo "Starting Playwright MCP server on port 8931..."
# We use the SSE transport version or a wrapper. 
# Usually 'npx @modelcontextprotocol/server-playwright' uses stdio. 
# For SSE, we might need a wrapper or use the mcp-proxy.
# However, the DB says http://localhost:8931/sse.
# I will use a simple npx command if it supports SSE, otherwise I'll use a known wrapper.
nohup npx -y @modelcontextprotocol/server-playwright --port 8931 > playwright_mcp.log 2>&1 &

# 2. LiveKit MCP (Debugging)
echo "Starting LiveKit MCP server..."
# The LiveKit MCP server usually connects via SSE or stdio.
# I'll run it on port 8932.
export LIVEKIT_URL=$LIVEKIT_URL
export LIVEKIT_API_KEY=$LIVEKIT_API_KEY
export LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET
nohup npx -y @livekit/mcp-server-livekit --port 8932 > livekit_mcp.log 2>&1 &

echo "MCP Servers started in background."
