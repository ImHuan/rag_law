import fitz  # PyMuPDF
from app.services.embedding_service import embed_model
from fastapi import UploadFile
from app.database.qdrant_db import get_vector_store
from config import settings
import logging

logger = logging.getLogger(__name__)

from langchain_text_splitters import RecursiveCharacterTextSplitter

async def extract_text_from_pdf(file: UploadFile) -> list[dict]:
    """
    Trích xuất toàn bộ văn bản từ file PDF được tải lên theo từng trang.
    
    Args:
        file (UploadFile): File PDF do người dùng tải lên thông qua API.
        
    Returns:
        list[dict]: Danh sách các dictionary, mỗi dictionary chứa văn bản của một trang ('text') và số trang tương ứng ('page').
    """
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        pages = []
        for i, page in enumerate(doc):
            pages.append({
                "text": page.get_text("text") + "\n",
                "page": i + 1
            })
        return pages
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise e

async def ingest_pdf(file: UploadFile, session_id: str = "default_session"):
    """
    Xử lý file PDF: trích xuất văn bản, chia nhỏ (chunking), tạo embedding và lưu vào Qdrant Vector Store.
    
    Args:
        file (UploadFile): File PDF cần xử lý.
        session_id (str, optional): ID của phiên làm việc để cô lập dữ liệu người dùng. Mặc định là "default_session".
        
    Returns:
        dict: Thông báo thành công và tổng số chunk đã được tạo và lưu trữ.
    """
    try:
        pages = await extract_text_from_pdf(file)
        if not pages:
            raise ValueError("No text found in PDF.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        chunks = []
        metadatas = []
        chunk_index = 0

        for page in pages:
            page_text = page["text"]
            if not page_text.strip():
                continue
            
            page_chunks = text_splitter.split_text(page_text)
            for c in page_chunks:
                chunks.append(c)
                metadatas.append({
                    "source": file.filename,
                    "page": page["page"],
                    "chunk_index": chunk_index,
                    "session_id": session_id
                })
                chunk_index += 1

        logger.info(f"Generated {len(chunks)} chunks from {file.filename}")

        vector_store = get_vector_store()
        await vector_store.aadd_texts(texts=chunks, metadatas=metadatas)
        
        logger.info(f"Successfully upserted {len(chunks)} points into {settings.QDRANT_COLLECTION_NAME}")
        return {"message": f"Successfully ingested {file.filename}", "chunks": len(chunks)}
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise e
