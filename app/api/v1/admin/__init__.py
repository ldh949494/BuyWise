"""Admin API router."""

from fastapi import APIRouter

from app.api.v1.admin.auth import router as auth_router
from app.api.v1.admin.products import router as products_router
from app.api.v1.admin.upload import router as upload_router


router = APIRouter(prefix="/admin")
router.include_router(auth_router, tags=["admin-auth"])
router.include_router(products_router, tags=["admin-products"])
router.include_router(upload_router, tags=["admin-upload"])
