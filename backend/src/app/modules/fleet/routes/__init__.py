"""Route exports for this domain module."""

from fastapi import APIRouter

from .roles import router as roles_router
from .router import router as fleet_router

router = APIRouter()
router.include_router(fleet_router)
router.include_router(roles_router)

__all__ = ["router"]
