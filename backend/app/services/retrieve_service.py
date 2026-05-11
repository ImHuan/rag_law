from app.services.embedding_service import embed_model
from app.database.qdrant_db import get_vector_store
from config import settings
import logging

logger = logging.getLogger(__name__)

async def retrieve_context(query: str, session_id: str = "default_session", top_k: int = 3):
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        vector_store = get_vector_store()
        
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.session_id",
                    match=MatchValue(value=session_id)
                )
            ]
        )

        search_result = await vector_store.asimilarity_search_with_score(
            query=query,
            k=top_k,
            filter=qdrant_filter
        )

        contexts = []
        for doc, score in search_result:
            contexts.append({
                "text": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            })
            
        logger.info(f"Retrieved {len(contexts)} relevant chunks for query.")
        return contexts

    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        raise e
