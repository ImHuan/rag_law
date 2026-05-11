from groq import AsyncGroq
from app.database.mongo_db import get_db
from app.services.retrieve_service import retrieve_context
from app.schemas.chat_io import ChatRequest, ChatResponse, SourceChunk
from config import settings
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def get_chat_history(session_id: str, limit: int = 5):
    db = get_db()
    history_cursor = db.chat_history.find({"session_id": session_id}).sort("timestamp", -1).limit(limit)
    history = await history_cursor.to_list(length=limit)
    history.reverse()
    
    formatted_history = []
    for msg in history:
        formatted_history.append({"role": "user", "content": msg["query"]})
        formatted_history.append({"role": "assistant", "content": msg["response"]})
    return formatted_history

async def save_chat_turn(session_id: str, query: str, response: str):
    db = get_db()
    await db.chat_history.insert_one({
        "session_id": session_id,
        "query": query,
        "response": response,
        "timestamp": datetime.utcnow()
    })

async def generate_response(request: ChatRequest) -> ChatResponse:
    """
    Tạo câu trả lời từ AI dựa trên câu hỏi của người dùng, ngữ cảnh truy xuất từ Qdrant và lịch sử chat.
    
    Args:
        request (ChatRequest): Đối tượng chứa câu hỏi (query) và session_id của người dùng.
        
    Returns:
        ChatResponse: Đối tượng chứa câu trả lời của AI và danh sách các nguồn tham khảo (sources) được sử dụng.
    """
    try:
        # Retrieve Context
        context_chunks = await retrieve_context(request.query, request.session_id)
        
        context_texts = []
        for chunk in context_chunks:
            source = chunk.get("metadata", {}).get("source", "Unknown")
            page = chunk.get("metadata", {}).get("page", "Unknown")
            text = chunk.get("text", "")
            context_texts.append(f"--- Nguồn: {source}, Trang: {page} ---\n{text}")
            
        context_text = "\n\n".join(context_texts)

        # Get Chat History
        history = await get_chat_history(request.session_id)

        # Construct System Prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
            
        system_prompt = prompt_template.format(context=context_text)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": request.query})

        # Call Groq LLM
        completion = await groq_client.chat.completions.create(
            messages=messages,
            model=settings.LLM_MODEL,
            temperature=0.5,
            max_tokens=1024,
        )
        
        ai_response = completion.choices[0].message.content

        # Save to MongoDB
        await save_chat_turn(request.session_id, request.query, ai_response)

        # Format Response
        sources = [SourceChunk(text=c["text"], score=c["score"], metadata=c["metadata"]) for c in context_chunks]
        return ChatResponse(response=ai_response, sources=sources)

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise e
