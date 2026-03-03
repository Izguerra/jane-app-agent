"""
Conversation history service for maintaining context across messages.
"""
from typing import List, Dict
from datetime import datetime, timedelta
from backend.database import SessionLocal, generate_message_id
from backend.models_db import ConversationMessage


class ConversationHistoryService:
    """Service for managing conversation history across channels."""
    
    @staticmethod
    def add_message(
        workspace_id: int,
        user_identifier: str,
        channel: str,
        role: str,
        content: str,
        communication_id: int = None
    ) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            workspace_id: The workspace ID
            user_identifier: Phone number, email, or user ID
            channel: "whatsapp", "sms", "web_chat", "voice"
            role: "user" or "assistant"
            content: The message content
            communication_id: Optional ID of the communication session
        """
        db = SessionLocal()
        try:
            message = ConversationMessage(
                id=generate_message_id(),
                workspace_id=workspace_id,
                user_identifier=user_identifier,
                channel=channel,
                role=role,
                content=content,
                communication_id=communication_id
            )
            db.add(message)
            
            # Update parent communication timestamp to keep session alive
            if communication_id:
                from backend.models_db import Communication
                from datetime import datetime, timezone
                
                comm = db.query(Communication).filter(Communication.id == communication_id).first()
                if comm:
                    comm.started_at = datetime.now(timezone.utc)
            
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def get_recent_history(
        workspace_id: int,
        user_identifier: str,
        channel: str,
        limit: int = 10,
        hours: int = 24,
        communication_id: int = None
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation history for a user.
        
        Args:
            workspace_id: The workspace ID
            user_identifier: Phone number, email, or user ID
            channel: "whatsapp", "sms", "web_chat", "voice"
            limit: Maximum number of messages to return
            hours: Only return messages from the last N hours
            
        Returns:
            List of messages in format [{"role": "user", "content": "..."}, ...]
        """
        db = SessionLocal()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = db.query(ConversationMessage).filter(
                ConversationMessage.workspace_id == workspace_id,
                ConversationMessage.user_identifier == user_identifier,
                ConversationMessage.channel == channel,
                ConversationMessage.created_at >= cutoff_time
            )
            
            if communication_id:
                query = query.filter(ConversationMessage.communication_id == communication_id)
                
            messages = query.order_by(
                ConversationMessage.created_at.desc()
            ).limit(limit).all()
            
            # Reverse to get chronological order (oldest to newest) for the agent
            messages.reverse()
            
            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        finally:
            db.close()
    
    @staticmethod
    def clear_old_messages(days: int = 30) -> int:
        """
        Clear messages older than N days (for cleanup/privacy).
        
        Args:
            days: Delete messages older than this many days
            
        Returns:
            Number of messages deleted
        """
        db = SessionLocal()
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            deleted = db.query(ConversationMessage).filter(
                ConversationMessage.created_at < cutoff_time
            ).delete()
            
            db.commit()
            return deleted
        finally:
            db.close()
