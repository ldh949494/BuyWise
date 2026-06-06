from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.compare import router as compare_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.guide_preferences import router as guide_preferences_router
from app.api.v1.health import router as health_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router
from app.api.v1.rag import router as rag_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.speech import router as speech_router
from app.api.v1.upload import router as upload_router
from app.api.v1.vision import router as vision_router


api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(products_router, tags=["products"])
api_router.include_router(orders_router, tags=["orders"])
api_router.include_router(feedback_router, tags=["feedback"])
api_router.include_router(guide_preferences_router, tags=["guide-preferences"])
api_router.include_router(reviews_router, tags=["reviews"])
api_router.include_router(compare_router, tags=["compare"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(rag_router, tags=["rag"])
api_router.include_router(upload_router, tags=["upload"])
api_router.include_router(vision_router, tags=["vision"])
api_router.include_router(speech_router, tags=["speech"])
