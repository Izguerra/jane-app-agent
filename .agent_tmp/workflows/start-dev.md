---
description: Start the full development environment (Database, Backend, Voice Agent, Frontend)
---

To run the application locally, you need to start four separate components.

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

### 3. Voice Agent (LiveKit Worker)
The voice agent handles real-time voice sessions.

```bash
# Terminal 2
source .venv/bin/activate
python -m backend.voice_agent dev
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
