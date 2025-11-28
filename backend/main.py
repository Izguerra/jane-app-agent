from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.routers import chat, knowledge, clinic, agent_settings, phone, analytics, voice, integrations

load_dotenv(override=True)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.database import init_db

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include Routers
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(clinic.router)
app.include_router(agent_settings.router)
app.include_router(phone.router)
app.include_router(analytics.router)
app.include_router(voice.router)
app.include_router(integrations.router)


