# ClauseCraft Migration Plan: Gradio → Next.js + FastAPI

## Executive Summary

Transform ClauseCraft from Gradio UI to a modern web architecture with Next.js frontend and FastAPI backend while preserving all existing functionality.

**Current Stack**: Gradio (Python UI framework), all-in-one monolithic app
**Target Stack**: Next.js 14 (TypeScript) + FastAPI (Python REST API)
**Timeline**: 3-5 days
**Risk**: Low (business logic modules remain unchanged)

---

## Why This Migration Makes Sense

✅ **Separation of Concerns**: Clean frontend/backend split
✅ **Professional UI**: Full control over design and UX
✅ **Scalability**: Easy to add features and pages
✅ **Modern Stack**: TypeScript, Tailwind CSS, React components
✅ **Existing Code Reuse**: [rag.py](rag.py), [classifier.py](classifier.py), [pdf_utils.py](pdf_utils.py) move as-is

---

## Current Architecture

```
app.py (642 lines)
├── Gradio UI (tabs, components)
├── PDF analysis logic
├── RAG query handling
└── Gemini LLM integration

Reusable Modules (no changes needed):
├── rag.py - ClauseStore with ChromaDB
├── classifier.py - ALBERT model wrapper
├── pdf_utils.py - PDF extraction
└── config.py - Environment configuration
```

---

## Target Architecture

```
┌─────────────────────────────────────────┐
│   Next.js Frontend (Port 3000)          │
│   ├── PDF Upload Page                   │
│   ├── Analysis Results Display          │
│   └── Chat/RAG Interface                │
└───────────────┬─────────────────────────┘
                │ REST API
┌───────────────┴─────────────────────────┐
│   FastAPI Backend (Port 8000)           │
│   ├── POST /api/pdf/analyze             │
│   ├── POST /api/chat/query              │
│   └── GET /api/kb/stats                 │
└───────────────┬─────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│   RAG   │ │Classifier│ │  Gemini  │
│(ChromaDB)│ │ (ALBERT) │ │   LLM    │
└─────────┘ └─────────┘ └──────────┘
```

---

## Directory Structure

```
clausecraft/
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                  # FastAPI app + CORS + routes
│   │   ├── config.py                # From existing config.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── pdf.py          # PDF analysis endpoints
│   │   │   │   ├── chat.py         # RAG query endpoints
│   │   │   │   └── kb.py           # Knowledge base stats
│   │   │   └── deps.py             # Dependency injection
│   │   ├── models/
│   │   │   ├── requests.py         # Pydantic request models
│   │   │   └── responses.py        # Pydantic response models
│   │   ├── services/
│   │   │   ├── rag.py              # From existing rag.py
│   │   │   ├── classifier.py       # From existing classifier.py
│   │   │   ├── pdf_utils.py        # From existing pdf_utils.py
│   │   │   └── llm.py              # Extracted from app.py
│   │   └── core/
│   │       └── errors.py           # Error handlers
│   ├── requirements.txt
│   └── .env
│
├── frontend/                         # Next.js application
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # PDF analysis page
│   │   └── chat/
│   │       └── page.tsx            # Chat interface page
│   ├── components/
│   │   ├── ui/                     # shadcn/ui components
│   │   ├── pdf/
│   │   │   ├── PDFUploader.tsx
│   │   │   └── AnalysisResults.tsx
│   │   └── chat/
│   │       ├── ChatInterface.tsx
│   │       ├── MessageList.tsx
│   │       └── KBStatsSidebar.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts           # Axios wrapper
│   │   │   ├── pdf.ts              # PDF API calls
│   │   │   └── chat.ts             # Chat API calls
│   │   └── hooks/
│   │       ├── usePDFAnalysis.ts
│   │       └── useChat.ts
│   ├── types/
│   │   ├── pdf.ts
│   │   └── chat.ts
│   ├── package.json
│   ├── .env.local
│   └── tailwind.config.ts
│
├── chroma_db/                       # Shared ChromaDB data
├── 9epochs-90 (1)/                  # Shared ALBERT model
└── run-all.sh                       # Start both services
```

---

## Implementation Steps

### Phase 1: Backend Setup (4-6 hours)

**1.1 Create Directory Structure**
```bash
mkdir -p backend/app/api/routes
mkdir -p backend/app/models
mkdir -p backend/app/services
mkdir -p backend/app/core
```

**1.2 Copy Existing Modules** (no changes needed)
```bash
cp config.py backend/app/config.py
cp rag.py backend/app/services/rag.py
cp classifier.py backend/app/services/classifier.py
cp pdf_utils.py backend/app/services/pdf_utils.py
```

**1.3 Create FastAPI Application**

Critical file: `backend/app/main.py`
- Initialize FastAPI app with lifespan event for ClauseStore
- Configure CORS to allow `http://localhost:3000`
- Include routers for pdf, chat, kb endpoints
- Add health check endpoint

**1.4 Create Pydantic Models**

Files: `backend/app/models/requests.py` and `responses.py`
- `PDFAnalysisRequest`: gemini_api_key
- `ChatMessage`: message, gemini_api_key, top_k
- `PDFAnalysisResponse`: classification_results, analysis_results, pages_processed, etc.
- `ChatResponse`: response, sources_used
- `KBStatistics`: total_clauses, red_flags_count, collection_name, status

**1.5 Setup Requirements**

File: `backend/requirements.txt`
```
fastapi>=0.108.0
uvicorn[standard]>=0.25.0
python-multipart>=0.0.6
pydantic>=2.5.0

# Existing dependencies
torch>=2.0.0
transformers>=4.36.0
PyPDF2>=3.0.0
google-generativeai>=0.3.0
chromadb>=0.4.22
sentence-transformers>=2.2.2
python-dotenv>=1.0.0
```

---

### Phase 2: API Endpoints (6-8 hours)

**2.1 PDF Analysis Endpoint**

File: `backend/app/api/routes/pdf.py`

```python
@router.post("/analyze", response_model=PDFAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    gemini_api_key: str = Form(...),
    clause_store: ClauseStore = Depends(get_clause_store)
):
    # 1. Validate PDF file
    # 2. Save to temp file
    # 3. Extract text by pages (pdf_utils.extract_text_by_pages)
    # 4. Store pages in RAG (clause_store.add_pdf_pages)
    # 5. Call Gemini for extraction/classification
    # 6. Return formatted results
    # 7. Clean up temp file
```

**2.2 LLM Service**

File: `backend/app/services/llm.py`

Extract from [app.py](app.py):
- `extract_and_analyze_with_llm()` - PDF analysis logic from app.py lines 100-200
- `generate_chat_response()` - Conversational RAG logic from app.py lines 250-350
- `build_conversation_context()` - History formatting
- `format_retrieved_clauses()` - RAG context formatting

**2.3 Chat Endpoint**

File: `backend/app/api/routes/chat.py`

```python
@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatMessage,
    history: List[ChatHistoryItem] = [],
    clause_store: ClauseStore = Depends(get_clause_store)
):
    # 1. Validate API key
    # 2. Convert history format
    # 3. Call generate_chat_response()
    # 4. Return response with sources
```

**2.4 Knowledge Base Stats Endpoint**

File: `backend/app/api/routes/kb.py`

```python
@router.get("/stats", response_model=KBStatistics)
async def get_kb_statistics(
    clause_store: ClauseStore = Depends(get_clause_store)
):
    # 1. Get stats from clause_store
    # 2. Count red flags
    # 3. Return formatted stats
```

**2.5 Error Handling**

File: `backend/app/core/errors.py`
- Setup global exception handlers
- Validation error handler (422)
- General exception handler (500)

---

### Phase 3: Frontend Setup (2-3 hours)

**3.1 Initialize Next.js Project**
```bash
npx create-next-app@latest frontend \
  --typescript --tailwind --app \
  --no-src-dir --import-alias "@/*"
```

**3.2 Install Dependencies**
```bash
cd frontend
npx shadcn-ui@latest init
npm install axios react-markdown remark-gfm react-dropzone
npm install @tanstack/react-query lucide-react
```

**3.3 Install shadcn/ui Components**
```bash
npx shadcn-ui@latest add button card input textarea tabs badge alert progress scroll-area separator skeleton
```

**3.4 Configure Environment**

File: `frontend/.env.local`
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

### Phase 4: Frontend Implementation (8-12 hours)

**4.1 API Client Setup**

File: `frontend/lib/api/client.ts`
- Create Axios instance with base URL
- Add response interceptor for error handling
- Set 2-minute timeout for PDF processing

File: `frontend/lib/api/pdf.ts`
- `analyzePDF()` - POST to /api/pdf/analyze with FormData

File: `frontend/lib/api/chat.ts`
- `sendChatMessage()` - POST to /api/chat/query
- `getKBStatistics()` - GET /api/kb/stats

**4.2 Type Definitions**

Files: `frontend/types/pdf.ts` and `chat.ts`
- `PDFAnalysisResult`, `AnalysisState`
- `Message`, `ChatState`

**4.3 Custom Hooks**

File: `frontend/lib/hooks/usePDFAnalysis.ts`
- Manages PDF analysis state (isAnalyzing, progress, error, result)
- `analyze()` function with progress simulation
- `reset()` function

File: `frontend/lib/hooks/useChat.ts`
- Manages chat state (messages, isLoading, error)
- `sendMessage()` with history tracking
- `clearMessages()` function

**4.4 PDF Components**

File: `frontend/components/pdf/PDFUploader.tsx`
- Drag-and-drop file upload with react-dropzone
- PDF validation
- File preview with size display
- Clear file functionality

File: `frontend/components/pdf/AnalysisResults.tsx`
- Markdown rendering with react-markdown + remark-gfm
- Scrollable card with syntax highlighting
- Classification and analysis display

**4.5 Chat Components**

File: `frontend/components/chat/ChatInterface.tsx`
- Message input with Textarea
- Send button with loading state
- Auto-scroll to bottom on new messages
- Enter to send (Shift+Enter for newline)

File: `frontend/components/chat/MessageList.tsx`
- User/assistant message bubbles
- Markdown rendering
- Source citations display

File: `frontend/components/chat/KBStatsSidebar.tsx`
- Real-time KB statistics
- Auto-refresh every 30 seconds
- Total clauses, red flags count
- Status badge

**4.6 Pages**

File: `frontend/app/page.tsx` (Main PDF Analysis Page)
- PDF uploader section
- API key input
- Analyze button with loading state
- Progress bar during analysis
- Two-column results display (classification + analysis)
- Instructions card

File: `frontend/app/chat/page.tsx` (Chat Interface Page)
- Chat interface with KB stats sidebar
- API key input
- Top-K slider (3-10 documents)
- Example queries list
- Navigation back to PDF analysis

File: `frontend/app/layout.tsx`
- Root layout with Inter font
- Metadata configuration
- Global styles

---

### Phase 5: Testing & Integration (4-6 hours)

**5.1 Backend Testing**

Start backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Test checklist:
- [ ] Server starts on port 8000
- [ ] http://localhost:8000/docs shows Swagger UI
- [ ] http://localhost:8000/health returns 200
- [ ] Test PDF upload with curl/Postman
- [ ] Verify CORS allows localhost:3000

**5.2 Frontend Testing**

Start frontend:
```bash
cd frontend
npm install
npm run dev
```

Test checklist:
- [ ] Server starts on port 3000
- [ ] PDF uploader accepts/rejects files correctly
- [ ] API key input works
- [ ] Analyze button triggers backend call
- [ ] Results display properly
- [ ] Chat interface sends/receives messages
- [ ] Navigation between pages works

**5.3 Integration Testing**

Full workflow test:
1. Upload a PDF from existing test documents
2. Verify classification results appear
3. Check ChromaDB stores pages (use KB stats)
4. Navigate to chat page
5. Send queries and verify RAG responses
6. Check source citations appear

---

### Phase 6: Deployment Preparation (2-4 hours)

**6.1 Development Scripts**

File: `run-all.sh` (project root)
```bash
#!/bin/bash
echo "🚀 Starting ClauseCraft"

# Start backend in background
cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ../frontend && npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
```

**6.2 Environment Configuration**

Backend `.env`:
```bash
GEMINI_API_KEY=your_key
GEMINI_MODEL=models/gemini-2.5-flash
MODEL_PATH=../9epochs-90 (1)
CHROMA_DB_PATH=../chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**6.3 Documentation**

Update README.md files in backend/ and frontend/ directories with:
- Setup instructions
- Environment variables
- Running locally
- API documentation links
- Troubleshooting guide

---

## Critical Files to Create/Modify

### Backend (New Files)
- `backend/app/main.py` - FastAPI entry point
- `backend/app/api/routes/pdf.py` - PDF analysis endpoint
- `backend/app/api/routes/chat.py` - Chat endpoint
- `backend/app/api/routes/kb.py` - KB stats endpoint
- `backend/app/services/llm.py` - Extract from app.py
- `backend/app/models/requests.py` - Pydantic models
- `backend/app/models/responses.py` - Pydantic models
- `backend/app/api/deps.py` - Dependency injection
- `backend/app/core/errors.py` - Error handlers
- `backend/requirements.txt` - Add FastAPI dependencies

### Frontend (New Directory)
- `frontend/app/page.tsx` - PDF analysis page
- `frontend/app/chat/page.tsx` - Chat page
- `frontend/lib/api/client.ts` - API client
- `frontend/lib/api/pdf.ts` - PDF API functions
- `frontend/lib/api/chat.ts` - Chat API functions
- `frontend/lib/hooks/usePDFAnalysis.ts` - PDF analysis hook
- `frontend/lib/hooks/useChat.ts` - Chat hook
- `frontend/components/pdf/PDFUploader.tsx` - File uploader
- `frontend/components/pdf/AnalysisResults.tsx` - Results display
- `frontend/components/chat/ChatInterface.tsx` - Chat UI
- `frontend/components/chat/MessageList.tsx` - Message display
- `frontend/components/chat/KBStatsSidebar.tsx` - Stats sidebar

### Reuse As-Is (Copy to Backend)
- [rag.py](rag.py) → `backend/app/services/rag.py`
- [classifier.py](classifier.py) → `backend/app/services/classifier.py`
- [pdf_utils.py](pdf_utils.py) → `backend/app/services/pdf_utils.py`
- [config.py](config.py) → `backend/app/config.py`

---

## API Endpoints Summary

| Method | Endpoint | Purpose | Request Body | Response |
|--------|----------|---------|--------------|----------|
| GET | `/health` | Health check | - | `{status, kb_clauses}` |
| POST | `/api/pdf/analyze` | Analyze PDF | `file, gemini_api_key` | `{classification_results, analysis_results, ...}` |
| POST | `/api/chat/query` | Chat query | `{message, gemini_api_key, top_k, history}` | `{response, sources_used}` |
| GET | `/api/kb/stats` | KB statistics | - | `{total_clauses, red_flags_count, ...}` |

---

## Verification Steps

### Backend Verification
1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Visit http://localhost:8000/docs (Swagger UI should load)
3. Test health endpoint: `curl http://localhost:8000/health`
4. Check CORS configuration allows frontend origin
5. Test PDF upload with a sample document
6. Verify ChromaDB connection and data persistence

### Frontend Verification
1. Start frontend: `cd frontend && npm run dev`
2. Visit http://localhost:3000
3. Test PDF upload UI (drag-and-drop + click)
4. Enter API key and analyze a PDF
5. Verify progress indicator shows
6. Check results render in markdown
7. Navigate to /chat page
8. Test chat interface with queries
9. Verify KB stats update

### Integration Verification
1. Full PDF analysis flow end-to-end
2. Chat retrieves relevant clauses from uploaded PDFs
3. Multiple PDFs accumulate in knowledge base
4. Source citations appear in chat responses
5. Error handling works (invalid files, missing API keys)

---

## Rollback Plan

If migration fails, you can immediately revert:
1. Stop Next.js and FastAPI servers
2. Return to using existing [app.py](app.py) with Gradio
3. ChromaDB data remains intact in [chroma_db/](chroma_db/)
4. No data loss - all business logic is preserved

---

## Success Criteria

Migration is complete when:
- ✅ Backend API responds correctly on port 8000
- ✅ Frontend loads on port 3000 with professional UI
- ✅ PDF upload and analysis works end-to-end
- ✅ Classification results display properly
- ✅ Chat interface provides RAG-grounded responses
- ✅ KB statistics update in real-time
- ✅ All Gradio functionality is replicated
- ✅ ChromaDB integration works
- ✅ Error handling is robust

---

## Timeline Estimate

| Phase | Duration |
|-------|----------|
| Phase 1: Backend Setup | 4-6 hours |
| Phase 2: API Endpoints | 6-8 hours |
| Phase 3: Frontend Setup | 2-3 hours |
| Phase 4: Frontend Implementation | 8-12 hours |
| Phase 5: Testing & Integration | 4-6 hours |
| Phase 6: Deployment Prep | 2-4 hours |
| **Total** | **26-39 hours (3-5 days)** |

---

## Notes

- **No Changes to Business Logic**: [rag.py](rag.py), [classifier.py](classifier.py), [pdf_utils.py](pdf_utils.py) work as-is
- **ChromaDB Compatibility**: Existing [chroma_db/](chroma_db/) data will work with new backend
- **Gradio Code Reference**: See [app.py](app.py) lines 100-200 for PDF analysis, lines 250-350 for chat logic
- **Parallel Development**: Can run both Gradio app and new stack simultaneously during testing
- **TypeScript Safety**: Frontend will catch API mismatches at compile time
- **Scalability**: Easy to add authentication, multi-user support, or new features later
