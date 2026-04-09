import logging
import asyncio
from datetime import datetime, timezone
from backend.database import SessionLocal
from backend.models_db import Communication, Workspace

logger = logging.getLogger("voice-handlers")

class VoiceHandlers:
    @staticmethod
    def register_session_events(session, ctx):
        @session.on("user_started_speaking")
        def on_user_started_speaking():
            logger.info("🎙️ USER STARTED SPEAKING")
            asyncio.create_task(ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"}))
            
        @session.on("user_stopped_speaking")
        def on_user_stopped_speaking():
            logger.info("🎙️ USER STOPPED SPEAKING")
            asyncio.create_task(ctx.room.local_participant.set_attributes({"lk.agent.state": "thinking"}))
            
        @session.on("agent_started_speaking")
        def on_agent_started_speaking():
            logger.info("🤖 AGENT STARTED SPEAKING")
            asyncio.create_task(ctx.room.local_participant.set_attributes({"lk.agent.state": "speaking"}))
            
        @session.on("agent_stopped_speaking")
        def on_agent_stopped_speaking():
            logger.info("🤖 AGENT STOPPED SPEAKING")
            asyncio.create_task(ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"}))

    @staticmethod
    async def capture_and_save_transcript(session, log_id, workspace_id, start_time):
        """Captures conversation history and updates the database log."""
        if not log_id: return

        transcript_items = []
        try:
            if session and hasattr(session, 'history'):
                for item in session.history.items:
                    role = getattr(item, 'role', 'unknown')
                    # Handle both method (older SDK) and property (newer SDK) for text_content
                    text_content_attr = getattr(item, 'text_content', None)
                    if callable(text_content_attr):
                        content = text_content_attr()
                    elif text_content_attr is not None:
                        content = text_content_attr
                    else:
                        content = getattr(item, 'content', '')
                    if isinstance(content, list): content = ' '.join(str(c) for c in content)
                    
                    system_indicators = ["SYSTEM INSTRUCTIONS:", "IDENTITY VERIFICATION", "GATEKEEPER RULE"]
                    if role != 'system' and content and not any(ind in content for ind in system_indicators):
                        transcript_items.append(f"{str(role).upper()}: {content}")

            db = SessionLocal()
            log = db.query(Communication).filter(Communication.id == log_id).first()
            if log:
                log.status = "completed"
                end_time = datetime.now(timezone.utc)
                log.ended_at = end_time
                
                transcript_text = "\n".join(transcript_items)
                log.transcript = transcript_text
                
                duration = (end_time - (log.started_at or start_time)).total_seconds()
                log.duration = int(duration)
                
                if workspace_id:
                    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                    if ws:
                        ws.voice_minutes_this_month = (ws.voice_minutes_this_month or 0) + max(1, int(duration/60))
                
                db.commit()
                
                if transcript_text:
                    await VoiceHandlers._trigger_analysis(log_id, transcript_text)
            db.close()
        except Exception as e:
            logger.error(f"Failed to capture transcript or update DB: {e}")

    @staticmethod
    async def _trigger_analysis(log_id, transcript_text):
        try:
            from backend.services.analysis_service import AnalysisService
            logger.info(f"Triggering analysis for {log_id}")
            await asyncio.wait_for(AnalysisService.analyze_communication(log_id, transcript_text), timeout=60.0)
        except Exception as e:
            logger.error(f"Analysis trigger failed: {e}")
