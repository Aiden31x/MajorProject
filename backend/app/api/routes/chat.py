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

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatMessage,
    clause_store: ClauseStore = Depends(get_clause_store)
):
    """
    Query the knowledge base with conversational RAG.
    
    Retrieves relevant clauses and generates contextual responses.
    """
    # Validate API key
    if not request.gemini_api_key or request.gemini_api_key.strip() == "":
        raise HTTPException(status_code=400, detail="Valid Gemini API key is required")
    
    # Convert history format from list of dicts to list of tuples
    history: List[Tuple[str, str]] = []
    for item in request.history:
        history.append((item.user, item.assistant))
    
    try:
        # Generate response using LLM service
        response_text, sources = generate_chat_response(
            message=request.message,
            history=history,
            gemini_api_key=request.gemini_api_key,
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
