from fastapi import APIRouter
from .general import router as general_router
from .security import router as security_router
from .api_keys import router as api_keys_router
from .integrations import router as integrations_router

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])

router.include_router(general_router)
router.include_router(security_router)
router.include_router(api_keys_router)
router.include_router(integrations_router)
