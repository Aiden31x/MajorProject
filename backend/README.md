# ClauseCraft Backend API

FastAPI backend for ClauseCraft lease agreement analyzer.

## Setup

1. **Create virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

4. **Run the server**:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### PDF Analysis
- `POST /api/pdf/analyze` - Analyze a PDF lease agreement
  - Request: `multipart/form-data` with `file` and `gemini_api_key`
  - Response: Classification and analysis results

### Chat
- `POST /api/chat/query` - Query knowledge base with RAG
  - Request: `{message, gemini_api_key, top_k, history}`
  - Response: AI-generated response with sources

### Knowledge Base
- `GET /api/kb/stats` - Get knowledge base statistics
  - Response: Total clauses, red flags count, status

### Health
- `GET /health` - Health check endpoint
- `GET /` - API information

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `BACKEND_PORT` - Port to run the server (default: 8000)
- `FRONTEND_URL` - Frontend URL for CORS (default: http://localhost:3000)
- `CHROMA_DB_PATH` - Path to ChromaDB storage (default: ../chroma_db)
- `MODEL_PATH` - Path to ALBERT model (default: ../9epochs-90 (1))

## Development

The backend uses:
- **FastAPI** - Modern Python web framework
- **ChromaDB** - Vector database for RAG
- **Google Gemini** - LLM for analysis and chat
- **ALBERT** - Fine-tuned model for clause classification
- **Sentence Transformers** - Text embeddings

## Testing

Visit http://localhost:8000/docs to test endpoints interactively with Swagger UI.

## Troubleshooting

**ChromaDB errors**: Make sure the `chroma_db` directory exists in the parent directory.

**Model loading errors**: Verify the `MODEL_PATH` in `.env` points to your ALBERT model directory.

**CORS errors**: Ensure `FRONTEND_URL` matches your frontend's URL.
