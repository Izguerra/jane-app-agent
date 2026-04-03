"""
╔══════════════════════════════════════════════════════════════════════╗
║  CRITICAL: PostgreSQL is the ONLY supported database.              ║
║                                                                    ║
║  DO NOT add SQLite fallback logic. DO NOT use sqlite:// URLs.      ║
║  If PostgreSQL is down, FIX PostgreSQL — do not switch databases.  ║
║                                                                    ║
║  The .env file MUST contain DATABASE_URL or POSTGRES_URL pointing  ║
║  to a valid PostgreSQL instance. This module will raise a hard     ║
║  error if no PostgreSQL URL is configured.                         ║
║                                                                    ║
║  This module is imported by LiveKit-spawned subprocesses           ║
║  (multiprocessing.spawn on macOS). The .env path MUST be absolute  ║
║  and derived from __file__, NOT from os.getcwd().                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import random
import string
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from backend.lib.id_service import IdService

_db_logger = logging.getLogger("backend.database")

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

# ── Load .env using ABSOLUTE path (critical for LiveKit subprocess safety) ──
# LiveKit agents run in spawned subprocesses (multiprocessing.spawn on macOS).
# Using load_dotenv() without an explicit path relies on os.getcwd() which may
# differ in the child process, causing DATABASE_URL to be None and silently
# creating a SQLite engine. This explicit path ensures .env is ALWAYS found.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

_db_logger.info(f"Loaded .env from: {_ENV_PATH} (exists={_ENV_PATH.exists()})")

# ── POSTGRESQL ENFORCEMENT ──
# Note: SQLite is ONLY permitted during unit/integration tests for speed and isolation.
# In all other environments (dev, staging, prod), PostgreSQL is strictly REQUIRED.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    raise ValueError(
        "FATAL: DATABASE_URL or POSTGRES_URL must be set in .env file.\n"
        f"Searched .env at: {_ENV_PATH}\n"
        "PostgreSQL is REQUIRED. Do NOT use SQLite. If PostgreSQL is down, fix PostgreSQL."
    )

# Hard-block SQLite unless we are explicitly in a test environment (pytest)
import sys
is_pytest = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
if "sqlite" in DATABASE_URL.lower() and not is_pytest:
    raise ValueError(
        f"FATAL: SQLite database URL detected: {DATABASE_URL}\n"
        "This application REQUIRES PostgreSQL in non-test environments. SQLite is NOT supported.\n"
        "Fix your DATABASE_URL in .env to point to a PostgreSQL instance."
    )

if "sslmode=require" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

# Fix postgres:// to postgresql:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_db_host = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'
print(f"[database] PostgreSQL connected: {_db_host}")
_db_logger.info(f"PostgreSQL engine configured: {_db_host}")

# Create engine — always PostgreSQL with connection pooling (unless testing with SQLite)
engine_kwargs = {
    "pool_pre_ping": True,
}

# These kwargs are only supported by PostgreSQL/MySQL dialects in SQLAlchemy
if "sqlite" not in DATABASE_URL.lower():
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
        User, Team, TeamMember, ActivityLog, PlatformIntegration,
        AdminSetting, APIKey, ActiveSession, Workspace, Agent,
        Communication, Integration, Document, Customer, ConversationMessage,
        PhoneNumber, WhatsAppTemplate, Appointment, Deal, AppointmentReminder,
        KnowledgeBaseSource, Campaign, CampaignStep, CampaignEnrollment,
        WorkerTemplate, WorkerTask, WorkerSchedule, WorkerInstance,
        Skill, AgentSkill, AgentPersonality, WorkspaceLLMConfig, MCPServer
    )
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


