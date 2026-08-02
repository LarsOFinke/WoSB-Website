"""Route exports for this domain module."""

from fastapi import APIRouter

from .printouts import router as printout_router
from .router import router as build_router

router = APIRouter()
router.include_router(printout_router)
router.include_router(build_router)

__all__ = ["router"]
