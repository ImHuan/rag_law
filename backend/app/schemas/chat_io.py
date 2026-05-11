from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"

class SourceChunk(BaseModel):
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceChunk] = []
