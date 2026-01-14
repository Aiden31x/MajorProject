# ClauseCraft v2.0 - Migration Complete! 🎉

**AI-Powered Lease Agreement Analyzer** with Next.js + FastAPI architecture

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### One-Command Startup

```bash
./run-all.sh
```

This will start both:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install

# Run frontend
npm run dev
```

## 📁 Project Structure

```
clausecraft/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # Configuration
│   │   ├── api/
│   │   │   ├── routes/        # API endpoints
│   │   │   └── deps.py        # Dependency injection
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Business logic
│   │   │   ├── rag.py        # RAG system
│   │   │   ├── classifier.py # ALBERT model
│   │   │   ├── pdf_utils.py  # PDF processing
│   │   │   └── llm.py        # Gemini LLM service
│   │   └── core/             # Error handlers
│   └── requirements.txt
│
├── frontend/                   # Next.js application
│   ├── app/
│   │   ├── page.tsx          # PDF analysis page
│   │   └── chat/page.tsx     # Chat interface
│   ├── components/           # React components
│   ├── lib/                  # API clients & hooks
│   └── types/                # TypeScript types
│
├── chroma_db/                 # Vector database (shared)
├── 9epochs-90 (1)/           # ALBERT model (shared)
└── run-all.sh                # Startup script
```

## ✨ Features

### PDF Analysis
- Upload lease agreement PDFs
- AI-powered clause extraction with Gemini LLM
- Automatic classification (red flags, rent terms, etc.)
- Page-by-page storage in vector database
- Historical context for better analysis

### RAG-Powered Chat
- Conversational queries about lease agreements
- Context-aware responses with source citations
- Adjustable retrieval parameters (top-k)
- Real-time knowledge base statistics
- Conversation history support

## 🛠 Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Axios** - API client
- **React Markdown** - Markdown rendering

### Backend
- **FastAPI** - Modern Python web framework
- **Google Gemini** - LLM for analysis and chat
- **ChromaDB** - Vector database for RAG
- **ALBERT** - Fine-tuned clause classification
- **Sentence Transformers** - Text embeddings
- **PyPDF2** - PDF text extraction

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/pdf/analyze` | Analyze PDF document |
| POST | `/api/chat/query` | Query with RAG |
| GET | `/api/kb/stats` | Knowledge base statistics |

Full API documentation: http://localhost:8000/docs

## 🔑 Environment Variables

### Backend (.env)
```bash
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=models/gemini-2.5-flash
MODEL_PATH=../9epochs-90 (1)
CHROMA_DB_PATH=../chroma_db
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🔄 Migration Summary

### What Changed
✅ **UI**: Gradio → Next.js 14 with professional design  
✅ **Backend**: Monolithic app.py → FastAPI REST API  
✅ **Architecture**: All-in-one → Clean frontend/backend separation  
✅ **Type Safety**: Python + TypeScript throughout  

### What Stayed the Same
✅ All business logic (rag.py, classifier.py, pdf_utils.py)  
✅ ChromaDB vector database  
✅ ALBERT model for classification  
✅ Gemini LLM integration  
✅ Complete feature parity with Gradio version  

## 🧪 Testing

### Backend
```bash
cd backend
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
# Development build
npm run dev

# Production build
npm run build
npm start
```

## 📚 Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Migration Plan](migration_plan.md)

## 🎯 Key Benefits

1. **Better UX**: Modern, responsive interface with smooth interactions
2. **Scalability**: Easy to add features, authentication, multi-user support
3. **Maintainability**: Clear separation of concerns, TypeScript safety
4. **Performance**: Optimized frontend, async API calls
5. **Developer Experience**: Hot reload, API docs, type checking

## 🐛 Troubleshooting

**Backend won't start**: Check if virtual environment is activated and dependencies are installed

**Frontend connection errors**: Verify backend is running on port 8000

**ChromaDB errors**: Ensure `chroma_db` directory exists with proper permissions

**Model loading errors**: Verify `MODEL_PATH` points to correct ALBERT model directory

## 📄 License

Same as original ClauseCraft project

## 🙏 Credits

Built on the original ClauseCraft Gradio application, migrated to modern web architecture while preserving all functionality.

---

**Version**: 2.0.0  
**Architecture**: Next.js 14 + FastAPI  
**LLM**: Google Gemini 2.5 Flash  
**Vector DB**: ChromaDB  
**Model**: ALBERT (fine-tuned)
