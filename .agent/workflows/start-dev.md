---
description: Start the full development environment (Database, Backend, Voice Agent, Avatar Agent, Frontend)
---

To run the application locally, you need to start five separate components.

### 1. Database (PostgreSQL)
Ensure Docker Desktop is running, then start the database container:

```bash
docker-compose up -d
```

### 2. Backend API (FastAPI)
The backend handles API requests from the frontend and database interactions.

```bash
# Terminal 1
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### 3. Unified Agent (Voice & Avatar)
The unified agent handles both phone calls and avatar sessions by routing based on room metadata.

```bash
# Terminal 2a
source .venv/bin/activate
python backend/voice_agent.py dev
```

### 3b. Unified Agent (Avatar)
```bash
# Terminal 2b
source .venv/bin/activate
python backend/avatar_agent.py dev
```

### 4. Frontend (Next.js)
The web dashboard.

```bash
# Terminal 3
npm run dev
```

### Verification
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Database: Port 54322
