from fastapi import APIRouter

from app.modules.admin.routes.backups import router as backups_router
from app.modules.admin.routes.content import router as content_router
from app.modules.admin.routes.ip_blocks import router as ip_blocks_router
from app.modules.admin.routes.legal_notice import router as legal_notice_router
from app.modules.admin.routes.logs import router as logs_router
from app.modules.admin.routes.master_data import router as master_data_router
from app.modules.admin.routes.outbound_webhooks import router as outbound_webhooks_router
from app.modules.admin.routes.registrations import router as registrations_router
from app.modules.admin.routes.system import router as system_router
from app.modules.admin.routes.users import router as users_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(system_router)
router.include_router(backups_router)
router.include_router(registrations_router)
router.include_router(logs_router)
router.include_router(ip_blocks_router)
router.include_router(legal_notice_router)
router.include_router(content_router)
router.include_router(users_router)
router.include_router(master_data_router)
router.include_router(outbound_webhooks_router)
