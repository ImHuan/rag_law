from langchain_huggingface import HuggingFaceEmbeddings
from config import settings
import logging

logger = logging.getLogger(__name__)

logger.info(f"Loading embedding model: {settings.EMBED_MODEL}")
embed_model = HuggingFaceEmbeddings(model_name=settings.EMBED_MODEL)
