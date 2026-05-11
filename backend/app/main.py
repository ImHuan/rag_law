from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routers import router
from app.database.mongo_db import MongoDB
from app.database.qdrant_db import QdrantDB
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lifecycle startup actions
    logger.info("Application starting up... Connecting to databases.")
    await MongoDB.connect()
    await QdrantDB.connect()
    
    yield
    
    # Lifecycle shutdown actions
    logger.info("Application shutting down... Disconnecting from databases.")
    await MongoDB.disconnect()
    await QdrantDB.disconnect()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG Backend API",
    description="FastAPI Backend for Retrieval-Augmented Generation using Qdrant, MongoDB, and Groq",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(router, prefix="/api/v1")

from fastapi.responses import FileResponse
import os

@app.get("/", tags=["Root"])
async def root():
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Welcome to the RAG FastAPI System. Visit /docs for the API documentation."}
