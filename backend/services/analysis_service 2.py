import logging
import os
import json
from backend.lib.ai_client import get_ai_client
from sqlalchemy.orm import Session
from backend.models_db import Communication
from backend.database import SessionLocal

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Service to perform AI analysis on communication transcripts.
    Generates Summary, Intent, and Outcome.
    """

    @staticmethod
    async def analyze_communication(communication_id: str, transcript: str):
        """
        Analyze the transcript to generate summary, intent, and outcome.
        Updates the Communication record in the database.
        """
        if not transcript or len(transcript.strip()) < 10:
            logger.info(f"Transcript too short for analysis (Comm ID: {communication_id})")
            return

        try:
            client, model_name = get_ai_client(async_mode=True)
        except Exception as e:
            logger.error(f"Failed to get AI client for analysis: {e}")
            return

        prompt = f"""
You are an expert conversation analyst. Analyze the following conversation transcript.

TRANSCRIPT:
{transcript}

TASK:
1. Summarize the conversation in 1-2 concise sentences.
2. Identify the primary Intent of the user (e.g., "Scheduling Appointment", "Sales Inquiry", "Customer Support", "General Question", "Complaint/Feedback").
3. Determine the Outcome of the interaction (e.g., "Appointment Booked", "Information Provided", "Follow-up Needed", "Voicemail Left", "Call Failed").
4. Determine the Sentiment of the user. BE CRITICAL.
   - "Positive": Happy, satisfied, grateful.
   - "Neutral": Matter-of-fact, information seeking, no strong emotion.
   - "Negative": Dissatisfied, complaining, frustrated, polite but critical (e.g., "I'm not happy", "bad experience").
   - If the user expresses ANY dissatisfaction, complaint, or negative feedback, mark as "Negative", even if they are polite.

OUTPUT FORMAT:
Return ONLY a JSON object with keys: "summary", "intent", "outcome", "sentiment".
"""

        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes conversations."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from AI analysis")
                return

            result = json.loads(content)
            
            summary = result.get("summary")
            intent = result.get("intent")
            outcome = result.get("outcome")
            sentiment = result.get("sentiment")

            logger.info(f"Analysis for {communication_id}: Intent={intent}, Outcome={outcome}, Sentiment={sentiment}")

            # Update Database
            db: Session = SessionLocal()
            try:
                comm = db.query(Communication).filter(Communication.id == communication_id).first()
                if comm:
                    comm.summary = summary
                    comm.call_intent = intent
                    comm.call_outcome = outcome
                    comm.sentiment = sentiment
                    
                    # Auto-Close Session on Terminal Outcome
                    TERMINAL_OUTCOMES = [
                        "Appointment Booked", 
                        "Appointment Rescheduled",
                        "Appointment Cancelled",
                        "Resolved", 
                        "Call Failed", 
                        "Voicemail Left", 
                        "Wrong Number"
                    ]
                    
                    # Case-insensitive check
                    if outcome and any(t.lower() in outcome.lower() for t in TERMINAL_OUTCOMES):
                        from datetime import datetime, timezone
                        comm.status = "completed"
                        if not comm.ended_at:
                            comm.ended_at = datetime.now(timezone.utc)
                        if comm.started_at and comm.ended_at:
                            comm.duration = int((comm.ended_at - comm.started_at).total_seconds())
                        logger.info(f"Auto-closing session {communication_id} due to terminal outcome: {outcome} (duration: {comm.duration}s)")

                    # Always update the transcript with the latest full version
                    if transcript and len(transcript) > len(comm.transcript or ""):
                        comm.transcript = transcript
                        
                    db.commit()
                    logger.info(f"Updated Communication {communication_id} with AI analysis.")
                    
                    # Trigger Dynamic CRM Analysis (MQL/SQL, Customer Type) using the transcript
                    # Must be done BEFORE closing the db session to avoid detached instance errors
                    if comm.customer_id:
                        try:
                            from backend.services.crm_service import CRMService
                            # New DB session for CRM analysis to isolate errors
                            cust_id = comm.customer_id # Capture ID string while attached
                            
                            crm_db = SessionLocal()
                            crm_service = CRMService(crm_db)
                            
                            # Log the attempt
                            logger.info(f"Triggering CRM Analysis for Customer {cust_id}")
                            
                            # 1. Update Lifecycle Stage (MQL/SQL/Lead)
                            analysis_result = crm_service.analyze_and_update_customer_status(
                                customer_id=cust_id,
                                interaction_text=transcript,
                                interaction_type="voice" if comm.type == "call" else "chat"
                            )
                            
                            if analysis_result.get("changed"):
                                logger.info(f"CRM Status Updated for {cust_id}: {analysis_result.get('updates')}")
    
                            # 2. Leads -> Customer conversion for appointments (The Reusable Component)
                            if outcome and "Appointment Booked" in outcome:
                                logger.info(f"Outcome is Appointment Booked. Triggering Lead -> Customer conversion for {cust_id}")
                                crm_service.convert_to_customer(cust_id, conversion_trigger="ai_analysis")
                                
                            crm_db.close()
                        except Exception as e:
                            logger.error(f"Failed to trigger CRM status update: {e}")
                            
            except Exception as e:
                logger.error(f"Database error updating analysis: {e}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to perform AI analysis: {e}")


def run_analysis_sync(communication_id: str, transcript: str):
    """
    Synchronous wrapper for analyze_communication.
    This is needed because FastAPI background_tasks doesn't properly await async functions.
    Using asyncio.run() ensures the async function completes fully.
    """
    import asyncio
    try:
        logger.info(f"Starting sync analysis for {communication_id}")
        asyncio.run(AnalysisService.analyze_communication(communication_id, transcript))
        logger.info(f"Completed sync analysis for {communication_id}")
    except Exception as e:
        logger.error(f"Sync wrapper error for analysis {communication_id}: {e}")
