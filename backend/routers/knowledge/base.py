from fastapi import APIRouter
from .sources import router as sources_router
from .files import router as files_router

router = APIRouter(prefix="/workspaces", tags=["Knowledge Base"])

router.include_router(sources_router)
router.include_router(files_router)
