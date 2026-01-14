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
    gemini_api_key: str = Field(..., description="Google Gemini API key for LLM access")
    top_k: int = Field(default=5, ge=3, le=10, description="Number of similar documents to retrieve")
    history: List[ChatHistoryItem] = Field(default=[], description="Conversation history")
