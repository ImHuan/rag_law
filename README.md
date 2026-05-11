# RAG cho Văn bản Pháp luật Việt Nam

Dự án này là một hệ thống RAG (Retrieval-Augmented Generation) được thiết kế đặc biệt để xử lý và trả lời các câu hỏi dựa trên Văn bản Pháp luật Việt Nam (Thông tư, Nghị định, v.v.). Hệ thống cho phép người dùng tải lên các tài liệu PDF và đặt câu hỏi, sau đó nhận được câu trả lời chính xác kèm theo trích dẫn nguồn (số trang, tên văn bản) để dễ dàng kiểm chứng.

## Cài đặt và Chạy ứng dụng

### Yêu cầu hệ thống
- Python 3.10+
- MongoDB đang chạy (local hoặc Atlas)
- Qdrant đang chạy (local hoặc Cloud)

### Các bước cài đặt

1. **Clone repository và di chuyển vào thư mục dự án:**
   ```bash
   git clone <repo-url>
   cd rag-project
   ```

2. **Tạo môi trường ảo và cài đặt thư viện:**
   ```bash
   python -m venv venv
   # Kích hoạt môi trường (Windows)
   venv\Scripts\activate
   # Kích hoạt môi trường (Mac/Linux)
   source venv/bin/activate
   
   pip install -r backend/requirements.txt
   ```

3. **Thiết lập biến môi trường:**
   Tạo file `.env` trong thư mục `backend/` với nội dung như sau:
   ```env
   GROQ_API_KEY=your_groq_api_key
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=your_qdrant_api_key_if_any
   MONGO_URI=mongodb://localhost:27017
   DB_NAME=rag_db
   ```

4. **Khởi chạy hệ thống:**
   Mở 2 terminal khác nhau:
   
   **Terminal 1 (Backend):**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
   
   **Terminal 2 (Frontend):**
   Mở trực tiếp file `frontend/index.html` trên trình duyệt của bạn (hoặc sử dụng Live Server trong VSCode).


## Kiến trúc Hệ thống (Architecture)

```text
rag-project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routers.py       # Tiếp nhận request (Endpoints)
│   │   ├── database/            # (Đã đổi tên từ models) Quy tắc lưu trữ
│   │   │   ├── mongo_db.py      # Cấu trúc lưu Chat History (MongoDB)
│   │   │   └── qdrant_db.py     # Cấu trúc lưu Vector Metadata (Qdrant)
│   │   ├── schemas/             # Quy tắc gửi/nhận dữ liệu (Pydantic)
│   │   │   └── chat_io.py       # Request/Response format
│   │   ├── prompts   
│   │   │   ├── system_prompt.txt          
│   │   ├── services/            
│   │   │   ├── ingest_service.py   # Input: PDF -> Vector -> DB
│   │   │   ├── retrieve_service.py # Search: Query -> Top K
│   │   │   └── generate_service.py # Output: Context + History -> LLM
│   │   └── main.py              # File chạy chính
│   │
│   ├── config.py                # Quản lý API Keys, URL
│   ├── .env                     # Lưu biến môi trường 
│   └── requirements.txt         # Thư viện cần cài
│
└── frontend/index.html
```

Quy trình hoạt động của hệ thống được chia làm 2 luồng chính:
1. **Luồng Ingestion (Xử lý tài liệu):** `PDF` → Trích xuất text (PyMuPDF) → Chia nhỏ văn bản (`RecursiveCharacterTextSplitter`) → Mã hóa (`HuggingFaceEmbeddings`) → Lưu trữ vào Vector DB (`Qdrant`). Mỗi session được tách biệt bằng `session_id`.
2. **Luồng Chat/Generation (Trả lời câu hỏi):** `Câu hỏi User` + `session_id` → Tìm kiếm Vector tương đồng (`Qdrant`) → Truy xuất Lịch sử Chat (`MongoDB`) → Tạo Prompt tổng hợp → Đưa vào LLM (`Groq / Llama 3`) → Trả về `Câu trả lời` + `Trích dẫn nguồn`.

---

## Các tính năng nổi bật (Highlights)

- **Kiến trúc Asynchronous & Quản lý Multi-Session:** Backend FastAPI được thiết kế xử lý bất đồng bộ, các luồng Ingest - Retrieve - Generate được tách biệt rõ ràng. Đặc biệt hệ thống xử lý tốt việc cô lập dữ liệu (Vector Context & Chat History) theo từng session_id, đảm bảo nhiều người có thể dùng cùng lúc mà không bị lẫn lộn ngữ cảnh.
- **Trích xuất nguồn minh bạch:** Câu trả lời được thiết kế để luôn truy xuất và hiển thị rõ ràng thông tin nguồn (độ tin cậy match score, số trang), một yếu tố rất quan trọng để tăng độ tin cậy khi làm việc với domain Văn bản Pháp luật.
- **Tốc độ phản hồi:** Việc kết hợp LLM inference qua Groq API và Qdrant Cloud giúp hệ thống đạt độ trễ cực thấp dù xử lý ngữ cảnh dài.

---

## Điểm hạn chế & Hướng phát triển (Limitations & Future Work)

- **Chiến lược Chunking chưa tối ưu cho luật:** Hiện tại hệ thống đang dùng RecursiveCharacterTextSplitter cắt theo số lượng ký tự. Việc này đôi khi làm đứt gãy ngữ nghĩa giữa các "Điều", "Khoản", "Điểm" trong văn bản luật pháp. Hướng cải thiện là dùng Rule-based Chunking (cắt theo regex của Điều/Khoản) hoặc Semantic Chunking.
- **Xử lý PDF phức tạp:** Chưa thể xử lý các file pdf được scan.
- **Mô hình Embedding:** Vector hóa đang dùng sentence-transformers mã nguồn mở chung. Độ chính xác tìm kiếm (retrieval) sẽ tốt hơn rất nhiều nếu mô hình này được fine-tune riêng trên bộ dữ liệu Tiếng Việt ngành luật.
