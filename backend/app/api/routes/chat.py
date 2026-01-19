"""
Chat and RAG Query Endpoints
"""
from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException

from app.models.requests import ChatMessage, ChatHistoryItem
from app.models.responses import ChatResponse
from app.services.llm import generate_chat_response
from app.services.rag import ClauseStore
from app.api.deps import get_clause_store
from app.config import GEMINI_API_KEY

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatMessage,
    clause_store: ClauseStore = Depends(get_clause_store)
):
    """
    Query the knowledge base with conversational RAG.

    Retrieves relevant clauses and generates contextual responses.

    Note: If gemini_api_key is not provided in request, the server's configured API key will be used.
    """
    # Use provided API key or fall back to server's configured key
    api_key_to_use = request.gemini_api_key if request.gemini_api_key and request.gemini_api_key.strip() else GEMINI_API_KEY

    # Validate API key
    if not api_key_to_use or api_key_to_use.strip() == "":
        raise HTTPException(status_code=400, detail="Valid Gemini API key is required (either provide one or configure GEMINI_API_KEY in backend .env)")

    # Convert history format from list of dicts to list of tuples
    history: List[Tuple[str, str]] = []
    for item in request.history:
        history.append((item.user, item.assistant))

    try:
        # Generate response using LLM service
        response_text, sources = generate_chat_response(
            message=request.message,
            history=history,
            gemini_api_key=api_key_to_use,
            clause_store=clause_store,
            top_k=request.top_k
        )
        
        return ChatResponse(
            response=response_text,
            sources_used=sources
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
