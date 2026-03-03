from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database import get_db
from backend.models_db import Communication
from backend.auth import get_current_user, AuthUser, get_workspace_context
from typing import List, Optional, Any
from datetime import datetime, timezone, timedelta


router = APIRouter(prefix="/communications", tags=["communications"])


@router.get("", include_in_schema=False)
@router.get("/")
async def get_communications(
    search: Optional[str] = "",
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    timeRange: Optional[str] = "7d", # 24h, 7d, 30d
    type: Optional[str] = None, # call, chat
    channel: Optional[str] = None, # whatsapp, etc
    agent_id: Optional[str] = Query(None, alias="agent"),
    direction: Optional[str] = None,
    call_intent: Optional[str] = None,
    call_outcome: Optional[str] = None,
    customer_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = None # Optional for backward compatibility if needed
):

    try:
        # Resolve workspace correctly
        workspace_id = get_workspace_context(db, user, workspace_id)
        
        try:
            if background_tasks:
                 from backend.services.crm_service import run_session_cleanup
                 background_tasks.add_task(run_session_cleanup, workspace_id)
        except Exception as e:
            pass
        
        query = db.query(Communication).filter(Communication.workspace_id == workspace_id)

        if type and type != 'all':
            query = query.filter(Communication.type == type)
        if channel and channel != 'all':
            query = query.filter(Communication.channel == channel)
        if agent_id and agent_id != 'all':
            query = query.filter(Communication.agent_id == agent_id)
        if direction and direction != 'all':
            query = query.filter(Communication.direction == direction)
        if call_intent:
            query = query.filter(Communication.call_intent == call_intent)
        if call_outcome:
            query = query.filter(Communication.call_outcome == call_outcome)
        if customer_id:
            query = query.filter(Communication.customer_id == customer_id)
        if campaign_id:
            query = query.filter(Communication.campaign_id == campaign_id)
        if start_date:
            query = query.filter(Communication.started_at >= start_date)
        if end_date:
            query = query.filter(Communication.started_at <= end_date)
            
        total = query.count()
        items = query.order_by(desc(Communication.started_at)).offset(offset).limit(limit).all()
        
        results = []
        for item in items:
            item_dict = {c.name: getattr(item, c.name) for c in item.__table__.columns}
            if 'transcript' not in item_dict:
                item_dict['transcript'] = None
            results.append(item_dict)
        
        return {
            "total": total,
            "items": results,
            "page": (offset // limit) + 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit,
            "has_next": offset + limit < total,
            "has_prev": offset > 0
        }
    except Exception as e:
        import traceback
        print(f"ERROR in get_communications: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{communication_id}")
def get_communication_details(
    communication_id: str,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user)
):
    """
    Get full details for a specific communication, including the transcript.
    """
    # Resolve workspace correctly
    workspace_id = get_workspace_context(db, user, workspace_id)
        
    comm = db.query(Communication).filter(
        Communication.id == communication_id,
        Communication.workspace_id == workspace_id
    ).first()
    
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    # If transcript is empty, try to reconstruct it from messages
    if not comm.transcript:
         # Lazy import to avoid circular dep if needed, but models_db is safe
         from backend.models_db import ConversationMessage
         
         messages = db.query(ConversationMessage).filter(
             ConversationMessage.communication_id == comm.id
         ).order_by(ConversationMessage.created_at.asc()).all()
         
         if messages:
             transcript_lines = []
             for msg in messages:
                 role_label = "USER" if msg.role == "user" else "ASSISTANT"
                 transcript_lines.append(f"{role_label}: {msg.content}")
             
             # We won't save it to DB here to avoid read-side side effects, 
             # but we'll return it in the response object
             # SQLAlchemy objects are mutable, so this works for the response serialization
             comm.transcript = "\n".join(transcript_lines)
             
             # Optional: If you WANT to save it permanently for faster future reads:
             # comm.transcript = "\n".join(transcript_lines)
             # db.commit() 
        
    # Serialize full object including transcript
    return comm


@router.post("/{communication_id}/analyze")
async def trigger_analysis(
    communication_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger AI analysis for a communication record.
    This endpoint is called by the voice agent after a call ends.
    The analysis runs in FastAPI background tasks, which survive the HTTP response.
    
    This is a public endpoint (no auth) because it's called by the voice agent worker process.
    Security: Communication ID is a NanoID, so it's effectively unguessable.
    """
    from backend.services.analysis_service import run_analysis_sync
    
    comm = db.query(Communication).filter(Communication.id == communication_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    
    transcript = comm.transcript
    if not transcript or len(transcript.strip()) < 10:
        return {"status": "skipped", "reason": "Transcript too short for analysis"}
    
    # Queue analysis in background using SYNC wrapper
    # The async analyze_communication doesn't work with background_tasks
    background_tasks.add_task(run_analysis_sync, communication_id, transcript)
    
    return {"status": "queued", "communication_id": communication_id}

