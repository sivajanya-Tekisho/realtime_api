from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
import asyncio

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Robust File Logging for debugging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server_debug.log"),
        logging.StreamHandler()
    ]
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permissive for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Start background services."""
    from app.api.endpoints.outbound import outbound_service
    logging.info("--- STARTUP: Initializing Outbound Queue Processor ---")
    if not outbound_service.is_running:
        asyncio.create_task(outbound_service.process_queue())

@app.get("/")
def read_root():
    return {"message": "Inbound Voice Assistant Backend is Running!"}

@app.get("/")
def root():
    return {"message": "Welcome to Inbound Voice Assistant API"}
