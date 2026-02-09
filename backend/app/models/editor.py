"""
Editor-specific models for TipTap document editor
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.document import PDFMetadata


class EditorClausePosition(BaseModel):
    """Clause position with absolute character positions for editor"""
    id: str = Field(..., description="UUID for React keys")
    clause_text: str = Field(..., description="Full text of the clause")
    absolute_start: int = Field(..., description="Position in concatenated full text")
    absolute_end: int = Field(..., description="End position in concatenated full text")
    page_number: int = Field(..., description="Original page number")
    risk_score: float = Field(..., description="Risk score (0-100)")
    risk_severity: str = Field(..., description="Risk severity level (Low/Medium/High)")
    risk_category: str = Field(..., description="Risk category (financial, legal, operational, etc.)")
    risk_explanation: str = Field(..., description="Explanation of why this clause is risky")
    recommended_action: str = Field(..., description="Recommended action to mitigate risk")
    confidence: float = Field(..., description="Confidence score (0-1)")


class EditorDocumentResponse(BaseModel):
    """Complete response for editor view"""
    full_text: str = Field(..., description="All pages concatenated with \\n\\n separators")
    clause_positions: List[EditorClausePosition] = Field(..., description="Clauses with absolute positions")
    page_boundaries: List[int] = Field(..., description="Character offsets where each page starts")
    risk_assessment: Dict[str, Any] = Field(..., description="Full risk assessment data")
    pdf_metadata: PDFMetadata = Field(..., description="PDF document metadata")
