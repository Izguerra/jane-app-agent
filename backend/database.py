import os
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from backend.lib.id_service import IdService

def generate_workspace_id(length=None):
    """Generate a workspace ID (K-Sortable)."""
    return IdService.generate("wrk")

def generate_team_id(length=None):
    """Generate a team/org ID (K-Sortable)."""
    return IdService.generate("org")

def generate_comm_id(length=None):
    """Generate a communication ID (K-Sortable)."""
    return IdService.generate("comm")

def generate_message_id(length=None):
    """Generate a message ID (K-Sortable)."""
    return IdService.generate("msg")

def generate_settings_id(length=None):
    """Generate an agent settings ID (K-Sortable)."""
    return IdService.generate("set")

def generate_integration_id(length=None):
    """Generate a unique ID for integrations"""
    return IdService.generate("int")

def generate_phone_id(length=None):
    """Generate a unique ID for phone numbers"""
    return IdService.generate("phn")

def generate_customer_id(length=None):
    """Generate a unique ID for customers with 'cust_' prefix"""
    return IdService.generate("cust")

def generate_guest_id(length=None):
    """Generate a unique ID for guests with 'guest_' prefix"""
    return IdService.generate("guest")

def format_session_id(client_uuid: str) -> str:
    """
    Format a client-generated UUID with the ann_ prefix for anonymous sessions.
    If already prefixed, return as-is.
    """
    if not client_uuid:
        return None
    if client_uuid.startswith("ann_"):
        return client_uuid
    return f"ann_{client_uuid}"

def generate_appointment_id(length=None):
    """Generate a unique ID for appointments"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=8)) # e.g. FRO530FN

def generate_agent_id(length=None):
    """Generate a unique ID for agents"""
    return IdService.generate("agnt")

def generate_deal_id(length=None):
    """Generate a unique ID for deals"""
    return IdService.generate("deal")

def generate_confirmation_code(length=6):
    """Generate a confirmation code for appointments"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

# Load environment variables from project root
load_dotenv()

# ALWAYS use PostgreSQL - no SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL or POSTGRES_URL must be set in .env file. PostgreSQL is required.")

if "sslmode=require" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

# Fix postgres:// to postgresql:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Using PostgreSQL database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")

# Create engine
engine_kwargs = {
    "pool_pre_ping": True
}

if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables if they don't exist
def init_db():
    from backend.models_db import (
        Agent, Workspace, Communication, Customer, ConversationMessage,
        Appointment, Deal, AppointmentReminder, WorkerInstance
    )
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


