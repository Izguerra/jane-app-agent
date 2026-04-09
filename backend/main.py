from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import nest_asyncio
import asyncio

# Load environment variables early
load_dotenv()

try:
    # Only apply nest_asyncio if strictly needed and not conflicting with uvloop
    # uvicorn uses uvloop by default on Mac/Linux which nest_asyncio can't patch
    nest_asyncio.apply()
except Exception:
    pass

# Import routers
from backend.routers import (
    chat,
    knowledge,
    workspace,
)
from backend.routers.knowledge import base as knowledge_base
from backend.routers import (
    agents,
    phone,
    analytics,
    voice,
    integrations,
    auth,
    public_agent,
    webhooks,
    instagram,
    meta_webhooks,
    phone_numbers,
    meta_auth,
    billing,
    communications,
    recordings,
    crm,
    customers,
    stripe_webhooks,
    settings,
    workspaces,
    admin_analytics,
    admin as admin_settings,
    appointments,
    deals,
    outbound,
    skills
)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Updated for credentials support
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Create uploads directory if it doesn't exist
upload_dir = Path("backend/data/uploads")
upload_dir.mkdir(parents=True, exist_ok=True)

# Mount uploads directory to serve static files
app.mount("/uploads", StaticFiles(directory="backend/data/uploads"), name="uploads")

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.get("/simple")
async def simple():
    return "ok"

@app.middleware("http")
async def log_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        print(f"GLOBAL ERROR caught in middleware: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}", "traceback": traceback.format_exc()}
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/db-test")
def db_test():
    """Test database connectivity explicitly"""
    try:
        from backend.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1")).scalar()
            return {"status": "ok", "result": result, "message": "Database connection successful"}
        finally:
            db.close()
    except Exception as e:
        import traceback
        print(f"DB Error: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def on_startup():
    from backend.database import init_db
    init_db()
    
    # Start Campaign Processor
    try:
        from backend.workers.campaign_worker import run_campaign_processor
        import asyncio
        asyncio.create_task(run_campaign_processor())
        print("Started Campaign Processor")
    except Exception as e:
        print(f"Failed to start campaign processor: {e}")
        
    # Session Cleanup Scheduler is now started in the main startup_event to avoid duplication.
    pass

# Combined API Router for /api prefix
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

# Include all standard routers into the api_router
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(workspace.router)
api_router.include_router(agents.router)
api_router.include_router(phone.router)
api_router.include_router(analytics.router)
api_router.include_router(voice.router)
api_router.include_router(voice.router, prefix="/agent")
api_router.include_router(integrations.router)
api_router.include_router(integrations.router, prefix="/agent")
api_router.include_router(auth.router)
api_router.include_router(public_agent.router)
api_router.include_router(webhooks.router)
api_router.include_router(instagram.router)
api_router.include_router(meta_webhooks.router)
api_router.include_router(phone_numbers.router)
api_router.include_router(phone_numbers.router, prefix="/agent")
api_router.include_router(meta_auth.router)
api_router.include_router(billing.router)
api_router.include_router(communications.router)
api_router.include_router(recordings.router)
api_router.include_router(crm.router)
api_router.include_router(settings.router)
api_router.include_router(settings.router, prefix="/agent")
api_router.include_router(customers.router)
api_router.include_router(stripe_webhooks.router)
api_router.include_router(workspaces.router)
api_router.include_router(admin_analytics.router)
api_router.include_router(admin_settings.router)
api_router.include_router(appointments.router)
api_router.include_router(deals.router)
api_router.include_router(outbound.router)
api_router.include_router(skills.router)
api_router.include_router(skills.router, prefix="/agent")
api_router.include_router(campaigns.router)
api_router.include_router(workers.router)
api_router.include_router(workers.router, prefix="/agent")
api_router.include_router(mcp_integrations.router)
api_router.include_router(mcp_integrations.router, prefix="/agent")
api_router.include_router(telnyx_router.router)

# Register the combined router to the app
app.include_router(api_router)

# Worker Executor lifecycle
from backend.workers import start_executor, stop_executor

@app.on_event("startup")
async def startup_event():
    """Start background worker executor on app startup."""
    import logging
    import asyncio
    from backend.services.scheduler_service import run_scheduler

    logger = logging.getLogger("uvicorn.error")
    # logger.info("Starting Worker Executor...")
    # start_executor()
    # logger.info("Worker Executor started")

    # Start Scheduler
    asyncio.create_task(run_scheduler())
    logger.info("Scheduler started")

    # Start Health Worker
    try:
        from backend.workers.health_worker import run_health_worker
        asyncio.create_task(run_health_worker())
        logger.info("Health Worker started")
    except Exception as e:
        logger.error(f"Failed to start Health Worker: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop worker executor on app shutdown."""
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info("Stopping Worker Executor...")
    stop_executor()
    logger.info("Worker Executor stopped")
