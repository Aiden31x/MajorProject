"""
Request models for ClauseCraft API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    """Single chat message in conversation history"""
    user: str
    assistant: str


class ChatMessage(BaseModel):
    """Chat query request"""
    message: str = Field(..., description="User's question about lease agreements")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API key for LLM access (optional, uses server key if not provided)")
    top_k: int = Field(default=5, ge=3, le=10, description="Number of similar documents to retrieve")
    history: List[ChatHistoryItem] = Field(default=[], description="Conversation history")


class NegotiationRequest(BaseModel):
    """Request to negotiate a risky lease clause"""
    clause_text: str = Field(..., description="Original risky clause text", min_length=10)
    clause_label: str = Field(..., description="Clause category/type (e.g., 'financial', 'termination')")
    risk_score: float = Field(..., description="Risk score (0-100)", ge=0, le=100)
    risk_explanation: str = Field(..., description="Why this clause is risky", min_length=10)
