from backend.agent import AgentManager
from backend.knowledge_base import KnowledgeBaseService

# Initialize Services
# These are singletons that can be imported by routers
agent_manager = AgentManager()
kb_service = KnowledgeBaseService()

def get_agent_manager():
    return agent_manager

def get_kb_service():
    return kb_service
