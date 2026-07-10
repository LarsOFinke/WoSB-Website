from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.home import router as home_router
from app.modules.accounts.routes.auth import router as auth_router
from app.modules.accounts.routes.profile import router as profile_router
from app.modules.admin.routes import router as admin_router
from app.modules.builds.routes import router as builds_router
from app.modules.calendar.routes import router as fleet_events_router
from app.modules.files.routes import router as files_router
from app.modules.fleet.routes import router as fleets_router
from app.modules.forum.routes import router as forum_router
from app.modules.groups.routes import router as groups_router
from app.modules.guides.routes import router as guides_router
from app.modules.ships.routes import router as ships_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(groups_router)
router.include_router(files_router)
router.include_router(fleets_router)
router.include_router(fleet_events_router)
router.include_router(forum_router)
router.include_router(guides_router)
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(home_router, tags=["home"])
router.include_router(profile_router)
router.include_router(ships_router)
router.include_router(builds_router)
