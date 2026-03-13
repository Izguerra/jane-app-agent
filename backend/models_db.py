from .database.models.utils import JSONB, ARRAY
from .database.models.auth import User, Team, TeamMember, APIKey, ActiveSession
from .database.models.workspace import Workspace, PlatformIntegration, MCPServer, Integration, WorkspaceLLMConfig
from .database.models.agent import Agent, Skill, AgentSkill, AgentPersonality
from .database.models.crm import Customer, Deal, Communication, ConversationMessage
from .database.models.scheduling import Appointment, AppointmentReminder, PhoneNumber, WhatsAppTemplate
from .database.models.worker import WorkerTemplate, WorkerTask, WorkerSchedule, WorkerInstance, Campaign, CampaignStep, CampaignEnrollment
from .database.models.knowledge import KnowledgeBaseSource, Document

# Ensure all models are available when importing from models_db
__all__ = [
    "User", "Team", "TeamMember", "APIKey", "ActiveSession",
    "Workspace", "PlatformIntegration", "MCPServer", "Integration", "WorkspaceLLMConfig",
    "Agent", "Skill", "AgentSkill", "AgentPersonality",
    "Customer", "Deal", "Communication", "ConversationMessage",
    "Appointment", "AppointmentReminder", "PhoneNumber", "WhatsAppTemplate",
    "WorkerTemplate", "WorkerTask", "WorkerSchedule", "WorkerInstance", 
    "Campaign", "CampaignStep", "CampaignEnrollment",
    "KnowledgeBaseSource", "Document",
    "JSONB", "ARRAY"
]
