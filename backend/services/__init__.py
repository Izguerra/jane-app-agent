_agent_manager = None
_kb_service = None
_worker_service = None

def get_agent_manager():
    global _agent_manager
    if _agent_manager is None:
        from backend.agent import AgentManager
        _agent_manager = AgentManager()
    return _agent_manager

def get_kb_service():
    global _kb_service
    if _kb_service is None:
        from backend.knowledge_base import KnowledgeBaseService
        _kb_service = KnowledgeBaseService()
    return _kb_service

def get_worker_service(db):
    """Get WorkerService instance with database session."""
    from backend.services.worker_service import WorkerService
    return WorkerService(db)

