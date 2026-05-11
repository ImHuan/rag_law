from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from app.services.embedding_service import embed_model
import logging
from config import settings

logger = logging.getLogger(__name__)

class QdrantDB:
    client: QdrantClient = None

    @classmethod
    async def connect(cls):
        try:
            cls.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            logger.info("Connected to Qdrant Cloud.")
            
            if not cls.client.collection_exists(settings.QDRANT_COLLECTION_NAME):
                from qdrant_client.models import VectorParams, Distance
                dummy_vector = embed_model.embed_query("test")
                cls.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(size=len(dummy_vector), distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
            
            try:
                from qdrant_client.models import PayloadSchemaType
                cls.client.create_payload_index(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    field_name="metadata.session_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
            except Exception as e:
                # Ignore if index already exists
                pass
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {e}")
            raise e

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from Qdrant.")

def get_qdrant_client() -> QdrantClient:
    if QdrantDB.client is None:
        raise Exception("QdrantClient is not initialized")
    return QdrantDB.client

def get_vector_store(collection_name: str = None) -> QdrantVectorStore:
    if QdrantDB.client is None:
        raise Exception("QdrantClient is not initialized")
    return QdrantVectorStore(
        client=QdrantDB.client,
        collection_name=collection_name or settings.QDRANT_COLLECTION_NAME,
        embedding=embed_model,
    )
