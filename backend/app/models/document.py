"""
Document Analysis Response Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class ClausePositionResponse(BaseModel):
    """Clause position data for frontend"""
    clause_text: str
    page_number: int
    start_char: int
    end_char: int
    risk_score: float
    risk_severity: str
    risk_category: str
    risk_explanation: str
    recommended_action: str
    confidence: float
    bounding_box: Optional[Dict[str, float]] = None
    validation_result: Optional[Dict[str, Any]] = None  # Validation result from validator agent


class PDFMetadata(BaseModel):
    """PDF file metadata"""
    total_pages: int
    file_size: int
    filename: str


class ClauseHighlightResponse(BaseModel):
    """Complete response for document analysis with clause highlighting"""
    risk_assessment: Dict[str, Any]  # Full risk assessment data
    clause_positions: List[ClausePositionResponse]
    pdf_metadata: PDFMetadata
    pdf_base64: str = Field(..., description="Base64-encoded PDF for frontend rendering")
