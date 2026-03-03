from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.auth import get_current_user, AuthUser, get_workspace_context
from backend.database import get_db
from backend.services.skill_service import SkillService
from backend.services.personality_service import PersonalityService
from backend.services.llm_provider_service import LLMProviderService

router = APIRouter(prefix="/skills", tags=["skills"])

class SkillCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    category: str
    instructions: str
    allowed_tools: Optional[List[str]] = None

class PersonalityUpdate(BaseModel):
    communication_style: Optional[str] = None
    core_values: Optional[str] = None
    tone_guide: Optional[str] = None
    good_examples: Optional[str] = None
    bad_examples: Optional[str] = None
    brand_voice: Optional[dict] = None

class BulkSkillToggle(BaseModel):
    enabled_skill_ids: List[str]

class LLMConfigUpdate(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    is_byok: bool = False
    api_key: Optional[str] = None

@router.get("")
async def list_skills(
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user, workspace_id)
    return SkillService.get_skills_catalog(db, workspace_id)

@router.post("")
async def create_custom_skill(
    skill_data: SkillCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user)
    return SkillService.create_custom_skill(
        db, 
        workspace_id, 
        skill_data.name, 
        skill_data.slug, 
        skill_data.category, 
        skill_data.instructions, 
        skill_data.allowed_tools
    )

@router.get("/agent/{agent_id}")
async def get_agent_skills(
    agent_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user)
    return SkillService.get_skills_for_agent(db, agent_id)

@router.post("/agent/{agent_id}/toggle/{skill_id}")
async def toggle_agent_skill(
    agent_id: str,
    skill_id: str,
    enabled: bool,
    request: Request,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user, workspace_id, request=request)
    return SkillService.toggle_skill(db, agent_id, skill_id, workspace_id, enabled)

@router.post("/agent/{agent_id}/bulk")
async def bulk_toggle_skills(
    agent_id: str,
    data: BulkSkillToggle,
    request: Request,
    workspace_id: Optional[str] = Query(None, alias="workspaceId"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk updates all skills for an agent."""
    workspace_id = get_workspace_context(db, current_user, workspace_id, request=request)
    SkillService.bulk_sync_skills(db, agent_id, workspace_id, data.enabled_skill_ids)
    return {"status": "success"}

@router.get("/agent/{agent_id}/personality")
async def get_personality(
    agent_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user)
    personality = PersonalityService.get_personality(db, agent_id)
    if personality and personality.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return personality

@router.put("/agent/{agent_id}/personality")
async def update_personality(
    agent_id: str,
    data: PersonalityUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user)
    return PersonalityService.save_personality(db, agent_id, workspace_id, data.model_dump())

@router.get("/workspace/llm-config")
async def get_llm_config(
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user)
    return LLMProviderService.get_config(db, workspace_id)

@router.put("/workspace/llm-config")
async def update_llm_config(
    data: LLMConfigUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace_id = get_workspace_context(db, current_user)
    return LLMProviderService.save_config(db, workspace_id, data.model_dump())
