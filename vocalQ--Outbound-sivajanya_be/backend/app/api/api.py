from fastapi import APIRouter
from app.api.endpoints import calls, websocket, admin, knowledge_base, outbound

api_router = APIRouter()
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(knowledge_base.router, tags=["knowledge-base"])
api_router.include_router(outbound.router, prefix="/outbound", tags=["outbound"])
