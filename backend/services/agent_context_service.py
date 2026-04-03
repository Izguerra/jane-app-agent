"""
Unified Agent Context Service

Provides cross-channel conversation memory by:
1. Resolving customer identity from any channel identifier
2. Fetching conversation history across ALL channels for a customer
3. Building context prompts for voice/avatar agents
4. Semantic retrieval from vector DB for long-term memory
"""
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from backend.database import SessionLocal
from backend.models_db import Customer, Communication, ConversationMessage

logger = logging.getLogger("agent-context-service")


class AgentContextService:
    """Service for unified cross-channel agent context memory."""

    # ──────────────────── Layer 1: Customer Resolution ────────────────────

    @staticmethod
    def resolve_customer(db: Session, workspace_id: str, identifier: str, channel: str = None) -> Optional[Customer]:
        """
        Resolve a customer from any identifier type (phone, email, auth_id, customer_id).
        
        Args:
            db: Database session
            workspace_id: The workspace ID
            identifier: Phone number, email, auth user ID, or customer ID
            channel: Optional channel hint for disambiguation
            
        Returns:
            Customer object or None
        """
        if not identifier:
            return None

        # 1. Direct customer ID match
        if identifier.startswith("cust_") or identifier.startswith("guest_"):
            customer = db.query(Customer).filter(
                Customer.id == identifier,
                Customer.workspace_id == workspace_id
            ).first()
            if customer:
                return customer

        # 2. Strip prefixes for auth-based identifiers
        clean_id = identifier.split("#")[0]  # Remove session suffix like "cust_xxx#session_123"
        if clean_id.startswith("usr_"):
            clean_auth_id = clean_id[4:]  # Remove usr_ prefix
            customer = db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                or_(
                    Customer.auth_user_id == clean_id,
                    Customer.auth_user_id == clean_auth_id
                )
            ).first()
            if customer:
                return customer

        # 3. Phone number match
        if identifier.startswith("+") or identifier.replace("-", "").replace(" ", "").isdigit():
            customer = db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                Customer.phone == identifier,
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer

        # 4. Email match
        if "@" in identifier:
            customer = db.query(Customer).filter(
                Customer.workspace_id == workspace_id,
                func.lower(Customer.email) == identifier.lower(),
                Customer.status != "deleted"
            ).first()
            if customer:
                return customer

        # 5. Fallback: look up via Communication records
        comm = db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.user_identifier == identifier,
            Communication.customer_id.isnot(None)
        ).order_by(desc(Communication.started_at)).first()

        if comm and comm.customer_id:
            return db.query(Customer).filter(Customer.id == comm.customer_id).first()

        return None

    # ──────────────────── Layer 2: Unified Context Retrieval ────────────────────

    @staticmethod
    def get_unified_context(
        db: Session,
        workspace_id: str,
        customer_id: str,
        limit: int = 20,
        hours: int = 72,
        exclude_communication_id: str = None
    ) -> List[Dict[str, str]]:
        """
        Fetch recent conversation messages across ALL channels for a customer.
        
        Uses the chain: Customer → Communication.customer_id → ConversationMessage.communication_id
        
        Args:
            db: Database session
            workspace_id: The workspace ID
            customer_id: The customer ID to fetch context for
            limit: Max number of messages to return
            hours: Only return messages from the last N hours
            exclude_communication_id: Optionally exclude current session's messages
            
        Returns:
            List of messages in format [{"role": "...", "content": "...", "channel": "...", "timestamp": "..."}]
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get all communication IDs for this customer in the workspace
        comm_query = db.query(Communication.id, Communication.channel).filter(
            Communication.workspace_id == workspace_id,
            Communication.customer_id == customer_id,
            Communication.started_at >= cutoff
        )

        if exclude_communication_id:
            comm_query = comm_query.filter(Communication.id != exclude_communication_id)

        comm_records = comm_query.all()

        if not comm_records:
            return []

        comm_ids = [c.id for c in comm_records]
        comm_channel_map = {c.id: c.channel for c in comm_records}

        # Fetch messages from ConversationMessage table
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.communication_id.in_(comm_ids),
            ConversationMessage.created_at >= cutoff
        ).order_by(
            desc(ConversationMessage.created_at)
        ).limit(limit).all()

        # Reverse to chronological order
        messages.reverse()

        # Also check for call transcripts in Communication records (voice/avatar)
        call_comms = db.query(Communication).filter(
            Communication.workspace_id == workspace_id,
            Communication.customer_id == customer_id,
            Communication.type == "call",
            Communication.transcript.isnot(None),
            Communication.started_at >= cutoff
        ).order_by(desc(Communication.started_at)).limit(5).all()

        result = []

        # Add call transcript summaries first (older context)
        for call in reversed(call_comms):
            if call.summary:
                result.append({
                    "role": "system",
                    "content": f"[Prior {call.channel or 'voice'} call summary]: {call.summary}",
                    "channel": call.channel or "voice",
                    "timestamp": call.started_at.isoformat() if call.started_at else ""
                })
            elif call.transcript and len(call.transcript) < 500:
                result.append({
                    "role": "system",
                    "content": f"[Prior {call.channel or 'voice'} call transcript]: {call.transcript}",
                    "channel": call.channel or "voice",
                    "timestamp": call.started_at.isoformat() if call.started_at else ""
                })

        # Add text messages
        for msg in messages:
            channel = comm_channel_map.get(msg.communication_id, msg.channel)
            result.append({
                "role": msg.role,
                "content": msg.content,
                "channel": channel,
                "timestamp": msg.created_at.isoformat() if msg.created_at else ""
            })

        return result[-limit:]  # Ensure we don't exceed limit after adding call context

    # ──────────────────── Layer 2b: Customer Summary ────────────────────

    @staticmethod
    def get_customer_summary(db: Session, customer_id: str) -> str:
        """
        Build a brief customer summary from CRM data.
        
        Args:
            db: Database session
            customer_id: The customer ID
            
        Returns:
            A formatted summary string for prompt injection
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return ""

        parts = []
        name_parts = []
        if customer.first_name:
            name_parts.append(customer.first_name)
        if customer.last_name:
            name_parts.append(customer.last_name)

        if name_parts:
            parts.append(f"Name: {' '.join(name_parts)}")
        if customer.email:
            parts.append(f"Email: {customer.email}")
        if customer.phone:
            parts.append(f"Phone: {customer.phone}")
        if customer.lifecycle_stage:
            parts.append(f"Stage: {customer.lifecycle_stage}")
        if customer.interaction_count:
            parts.append(f"Total interactions: {customer.interaction_count}")

        if not parts:
            return ""

        return "KNOWN CUSTOMER INFO:\n" + "\n".join(f"- {p}" for p in parts)

    # ──────────────────── Layer 3: Voice/Avatar Prompt Builder ────────────────────

    @staticmethod
    def build_context_prompt(
        workspace_id: str,
        identifier: str,
        channel: str = None,
        limit: int = 10,
        hours: int = 72,
        agent_id: str = None
    ) -> str:
        """
        Build a context section for voice/avatar system prompts.
        
        This is the main entry point for voice and avatar agents — it resolves
        the customer, fetches cross-channel history, and formats it as a prompt section.
        
        Args:
            workspace_id: The workspace ID
            identifier: Any identifier (phone, email, customer_id, etc.)
            channel: Optional channel hint
            limit: Max messages to include
            hours: Lookback window
            
        Returns:
            Formatted context string for prompt injection, or empty string
        """
        db = SessionLocal()
        try:
            customer = AgentContextService.resolve_customer(db, workspace_id, identifier, channel)
            if not customer:
                return ""

            # Get customer summary
            summary = AgentContextService.get_customer_summary(db, customer.id)

            # Get cross-channel history
            context_messages = AgentContextService.get_unified_context(
                db, workspace_id, customer.id, limit=limit, hours=hours
            )

            if not context_messages and not summary:
                return ""

            prompt_parts = []

            if summary:
                prompt_parts.append(summary)

            if context_messages:
                prompt_parts.append("\nPRIOR CONVERSATION CONTEXT (across all channels):")
                for msg in context_messages:
                    channel_tag = f" [{msg['channel']}]" if msg.get('channel') else ""
                    role_label = msg['role'].upper()
                    prompt_parts.append(f"  {role_label}{channel_tag}: {msg['content']}")

                prompt_parts.append(
                    "\nUse the above context to provide a seamless, personalized experience. "
                    "Reference prior interactions naturally when relevant."
                )

            return "\n".join(prompt_parts)
        except Exception as e:
            logger.error(f"Failed to build context prompt: {e}")
            return ""
        finally:
            db.close()

    # ──────────────────── Layer 3b: Vector Search (Semantic) ────────────────────

    @staticmethod
    def get_relevant_context(
        workspace_id: str,
        query: str,
        user_identifier: str = None,
        limit: int = 5
    ) -> List[str]:
        """
        Use vector similarity search to retrieve relevant past conversations.
        Falls back gracefully if vector service is unavailable.
        
        Args:
            workspace_id: The workspace ID
            query: The current user message/query
            user_identifier: Optional filter by user
            limit: Max results
            
        Returns:
            List of relevant context strings
        """
        try:
            from backend.services.vector_sync import get_kb_service
            kb_service = get_kb_service()
            if not kb_service:
                return []

            # Build metadata filter
            metadata_filter = {"workspace_id": workspace_id, "type": "chat_message"}
            if user_identifier:
                metadata_filter["user_identifier"] = str(user_identifier)

            results = kb_service.query(query, top_k=limit, filter=metadata_filter)

            context_items = []
            for result in results:
                if hasattr(result, 'metadata') and hasattr(result, 'text'):
                    channel = result.metadata.get('channel', 'unknown')
                    role = result.metadata.get('role', 'unknown')
                    context_items.append(f"[{channel}/{role}] {result.text}")

            return context_items
        except Exception as e:
            logger.debug(f"Vector search unavailable: {e}")
            return []

    # ──────────────────── Convenience: Enrich History for Text Channels ────────────────────

    @staticmethod
    def enrich_history(
        workspace_id: str,
        identifier: str,
        current_history: List[Dict],
        communication_id: str = None,
        channel: str = None
    ) -> List[Dict]:
        """
        Enrich the current session's history with cross-channel context.
        Used by the orchestrator for chatbot, WhatsApp, and SMS.
        
        Args:
            workspace_id: The workspace ID
            identifier: User identifier for customer resolution
            current_history: The current session's message history
            communication_id: Current session ID to exclude from cross-channel results
            channel: Current channel
            
        Returns:
            Enriched history list with cross-channel context prepended
        """
        db = SessionLocal()
        try:
            customer = AgentContextService.resolve_customer(db, workspace_id, identifier, channel)
            if not customer:
                return current_history

            # Get cross-channel context (excluding current session)
            cross_channel = AgentContextService.get_unified_context(
                db, workspace_id, customer.id,
                limit=10, hours=72,
                exclude_communication_id=communication_id
            )

            if not cross_channel:
                return current_history

            # Build a system message summarizing prior context
            context_lines = []
            for msg in cross_channel:
                ch = msg.get('channel', '')
                context_lines.append(f"[{ch}] {msg['role'].upper()}: {msg['content']}")

            if not context_lines:
                return current_history

            # Get customer summary
            summary = AgentContextService.get_customer_summary(db, customer.id)

            system_context = "PRIOR CROSS-CHANNEL CONTEXT:\n"
            if summary:
                system_context += summary + "\n\n"
            system_context += "Recent interactions from other channels:\n"
            system_context += "\n".join(context_lines[-10:])
            system_context += "\n\nUse this context to provide continuity across channels."

            # Prepend as a system message
            enriched = [{"role": "system", "content": system_context}]
            enriched.extend(current_history)
            return enriched

        except Exception as e:
            logger.error(f"Failed to enrich history: {e}")
            return current_history
        finally:
            db.close()
