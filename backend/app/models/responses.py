"""
Response models for ClauseCraft API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PDFAnalysisResponse(BaseModel):
    """Response from PDF analysis endpoint"""
    classification_results: str = Field(..., description="Markdown-formatted classification results")
    analysis_results: str = Field(..., description="Markdown-formatted analysis results")
    pages_processed: int = Field(..., description="Number of pages processed from PDF")
    total_characters: int = Field(..., description="Total characters extracted from PDF")
    source_document: str = Field(..., description="Original filename")
    stored_in_kb: bool = Field(..., description="Whether pages were stored in knowledge base")
    total_kb_count: int = Field(..., description="Total documents/pages in knowledge base after this upload")


class ChatResponse(BaseModel):
    """Response from chat query endpoint"""
    response: str = Field(..., description="AI-generated response to user query")
    sources_used: List[str] = Field(default=[], description="List of source documents cited")


class KBStatistics(BaseModel):
    """Knowledge base statistics"""
    total_clauses: int = Field(..., description="Total number of clauses/pages in KB")
    red_flags_count: int = Field(default=0, description="Number of red flag clauses detected")
    collection_name: str = Field(..., description="ChromaDB collection name")
    status: str = Field(..., description="Status message (e.g., 'Ready for queries')")
