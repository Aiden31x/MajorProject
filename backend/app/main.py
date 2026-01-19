"""
ClauseCraft FastAPI Backend
Main application with routes and lifecycle management
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import FRONTEND_URL, ALLOWED_ORIGINS
from app.services.rag import ClauseStore
from app.api import deps
from app.api.routes import pdf, chat, kb, document
from app.core.errors import validation_exception_handler, general_exception_handler


# Global clause store instance
clause_store_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    global clause_store_instance
    print("=" * 60)
    print("🏢 ClauseCraft FastAPI Backend")
    print("=" * 60)
    print("\n📦 Initializing RAG system...")
    
    try:
        clause_store_instance = ClauseStore()
        deps.set_clause_store(clause_store_instance)
        print("✅ RAG system initialized successfully!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        raise
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down ClauseCraft backend...")


# Create FastAPI app
app = FastAPI(
    title="ClauseCraft API",
    description="AI-Powered Lease Agreement Analyzer with RAG",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS.split(",") if isinstance(ALLOWED_ORIGINS, str) else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(pdf.router)
app.include_router(chat.router)
app.include_router(kb.router)
app.include_router(document.router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        stats = clause_store_instance.get_statistics() if clause_store_instance else {}
        return {
            "status": "healthy",
            "service": "ClauseCraft API",
            "kb_clauses": stats.get('total_clauses', 0)
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "ClauseCraft API",
            "error": str(e)
        }


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "ClauseCraft API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }
