import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv()

# Use SQLite for development if PostgreSQL is not available or connection fails
# This allows the app to work without requiring PostgreSQL setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("POSTGRES_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    # Test connection if Postgres is configured
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            pass
except Exception as e:
    print(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
    DATABASE_URL = None

if not DATABASE_URL:
    # Default to SQLite for development
    import pathlib
    db_path = pathlib.Path(__file__).parent / "jane_agent.db"
    DATABASE_URL = f"sqlite:///{db_path}"
    print(f"Using SQLite database at: {db_path}")

# For SQLite, we need check_same_thread=False to allow multiple threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables if they don't exist (for SQLite development)
def init_db():
    from backend.models_db import AgentSettings, Clinic, KnowledgeDocument, CommunicationLog
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

