from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models_db import CommunicationLog as CommunicationLogModel

router = APIRouter(prefix="/analytics", tags=["analytics"])

class CommunicationLog(BaseModel):
    id: int
    type: str
    direction: str
    status: str
    duration: int
    started_at: datetime
    sentiment: Optional[str] = None

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_calls: int
    total_chats: int
    missed_calls: int
    avg_duration: float
    sentiment_score: float # 0 to 100

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: Session = Depends(get_db)):
    try:
        # Total Calls
        total_calls = db.query(CommunicationLogModel).filter(CommunicationLogModel.type == 'call').count()
        
        # Total Chats
        total_chats = db.query(CommunicationLogModel).filter(CommunicationLogModel.type == 'chat').count()
        
        # Missed Calls
        missed_calls = db.query(CommunicationLogModel).filter(
            CommunicationLogModel.type == 'call', 
            CommunicationLogModel.status == 'missed'
        ).count()
        
        # Avg Duration (calls only)
        avg_duration_result = db.query(func.avg(CommunicationLogModel.duration)).filter(CommunicationLogModel.type == 'call').scalar()
        avg_duration = float(avg_duration_result) if avg_duration_result else 0.0
        
        # Sentiment Score (mock for now as we don't have sentiment analysis yet)
        sentiment_score = 85.0 
        
        return AnalyticsSummary(
            total_calls=total_calls,
            total_chats=total_chats,
            missed_calls=missed_calls,
            avg_duration=round(avg_duration, 1),
            sentiment_score=sentiment_score
        )
    except Exception as e:
        print(f"Error fetching analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[CommunicationLog])
async def get_communication_history(db: Session = Depends(get_db)):
    try:
        logs = db.query(CommunicationLogModel).order_by(CommunicationLogModel.started_at.desc()).limit(50).all()
        return logs
    except Exception as e:
        print(f"Error fetching communication history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
