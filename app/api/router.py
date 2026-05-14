from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.compare import router as compare_router
from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.api.v1.rag import router as rag_router
from app.api.v1.speech import router as speech_router
from app.api.v1.upload import router as upload_router
from app.api.v1.vision import router as vision_router


api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(products_router, tags=["products"])
api_router.include_router(compare_router, tags=["compare"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(rag_router, tags=["rag"])
api_router.include_router(upload_router, tags=["upload"])
api_router.include_router(vision_router, tags=["vision"])
api_router.include_router(speech_router, tags=["speech"])
