from fastapi import APIRouter
from . import crud, logic

router = APIRouter(prefix="/agents", tags=["agents"])

# Include sub-routers
router.include_router(crud.router)
router.include_router(logic.router)

@router.get("/options")
async def get_agent_options():
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy"},
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (ElevenLabs)"},
        ],
        "languages": [
            {"id": "en", "name": "English"},
            {"id": "es", "name": "Spanish"},
        ]
    }
