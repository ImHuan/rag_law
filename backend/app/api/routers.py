from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.schemas.chat_io import ChatRequest, ChatResponse
from app.services.ingest_service import ingest_pdf
from app.services.generate_service import generate_response

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(file: UploadFile = File(...), session_id: str = Form("default_session")):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        result = await ingest_pdf(file, session_id)
        return result
    except Exception as e:
        logger.error(f"Ingestion endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await generate_response(request)
        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during chat generation.")
