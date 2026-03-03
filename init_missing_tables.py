
from backend.database import engine, Base
from backend.models_db import (
    Agent, Workspace, Communication, Customer, ConversationMessage,
    Appointment, Deal, AppointmentReminder, WorkerInstance,
    AgentSkill, AgentPersonality
)

def init_all():
    print("Initializing all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    init_all()
