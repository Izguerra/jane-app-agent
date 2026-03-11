from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global instance
_kb_service = None

def get_kb_service():
    global _kb_service
    if _kb_service is None:
        try:
            logger.info("Initializing KnowledgeBaseService...")
            from backend.knowledge_base import KnowledgeBaseService
            _kb_service = KnowledgeBaseService()
            logger.info("KnowledgeBaseService initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeBaseService: {e}")
            _kb_service = False # Marker for failed init to avoid retry loop
    
    if _kb_service is False:
        return None
    return _kb_service


def sync_chat_message(workspace_id: int, user_identifier: str, channel: str, role: str, content: str):
    """
    Syncs a single chat message to the vector database.
    """
    kb_service = get_kb_service()
    if not kb_service or not content:
        return

    try:
        doc_id = f"msg_{workspace_id}_{user_identifier}_{datetime.now().timestamp()}"
        metadata = {
            "workspace_id": workspace_id,
            "user_identifier": str(user_identifier),
            "channel": str(channel),
            "role": str(role),
            "type": "chat_message",
            "timestamp": datetime.now().isoformat()
        }
        kb_service.upsert_document(doc_id, content, metadata)
        logger.info(f" synced chat message to vector db: {doc_id}")
    except Exception as e:
        logger.error(f"Error syncing chat message to vector db: {e}")

def sync_call_transcript(workspace_id: int, user_identifier: str, transcript: str, summary: str, call_id: int):
    """
    Sync call transcript and summary to Pinecone Vector DB.
    """
    kb_service = get_kb_service()
    if not kb_service:
        return

    try:
        # Upsert Transcript
        if transcript:
            doc_id_trans = f"call_{call_id}_transcript"
            metadata_trans = {
                "workspace_id": workspace_id,
                "user_identifier": str(user_identifier),
                "channel": "phone_call",
                "role": "mixed",
                "type": "call_transcript",
                "timestamp": datetime.now().isoformat()
            }
            kb_service.upsert_document(doc_id_trans, transcript, metadata_trans)
        
        # Upsert Summary
        if summary:
            doc_id_sum = f"call_{call_id}_summary"
            metadata_sum = {
                "workspace_id": workspace_id,
                "user_identifier": str(user_identifier),
                "channel": "phone_call",
                "role": "mixed",
                "type": "call_summary",
                "timestamp": datetime.now().isoformat()
            }
            kb_service.upsert_document(doc_id_sum, summary, metadata_sum)
            
        logger.info(f"Synced call {call_id} to vector db")
    except Exception as e:
        logger.error(f"Error syncing call to vector db: {e}")

def sync_agent_soul(workspace_id: str, agent_id: str, soul_content: str):
    """
    Syncs the agent's soul (core identity) to the vector database.
    This allows the agent's core identity to be searchable or retrieved during RAG.
    """
    kb_service = get_kb_service()
    if not kb_service or not soul_content:
        return

    try:
        doc_id = f"agent_soul_{agent_id}"
        metadata = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "type": "agent_soul",
            "timestamp": datetime.now().isoformat()
        }
        kb_service.upsert_document(doc_id, soul_content, metadata)
        logger.info(f"Synced agent soul to vector db: {doc_id}")
    except Exception as e:
        logger.error(f"Error syncing agent soul to vector db: {e}")
