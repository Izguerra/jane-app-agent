---
description: Global rule - Always restart frontend/backend/LiveKit servers before running E2E tests
---

## Pre-E2E Test Server Restart

**Before running any E2E (end-to-end) tests**, you MUST restart the following services in this order:

### 1. Stop Existing Servers
Kill any running instances of:
- Frontend (Next.js dev server on port 3000)
- Backend (FastAPI/uvicorn on port 8000)
- Voice/Avatar agents

### 2. Restart Backend
```bash
# Terminal 1
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### 3. Restart Frontend
```bash
# Terminal 2
npm run dev
```

### 4. Restart LiveKit Agents (if testing voice/avatar)
```bash
# Terminal 3
source .venv/bin/activate
python backend/voice_agent.py dev
```

```bash
# Terminal 4
source .venv/bin/activate
python backend/avatar_agent.py dev
```

### 5. Wait for Ready
- Backend: Wait for "Application startup complete"
- Frontend: Wait for "Ready in X.Xs"
- Only then proceed with browser-based E2E tests

### Why
Fresh server restarts ensure:
- All code changes are loaded
- No stale cached state
- No zombie connections
- Clean LiveKit room state
