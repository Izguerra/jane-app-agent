from fastapi import APIRouter
from .templates import router as templates_router
from .instances import router as instances_router
from .tasks import router as tasks_router

router = APIRouter(prefix="/workers", tags=["Workers"])

router.include_router(templates_router)
router.include_router(instances_router)
router.include_router(tasks_router)
