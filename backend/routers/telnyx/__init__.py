from fastapi import APIRouter
from .calls import router as calls_router
from .sms import router as sms_router

router = APIRouter(prefix="/telnyx", tags=["Telnyx"])

router.include_router(calls_router)
router.include_router(sms_router)
