"""
Response models for ClauseCraft API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ClauseRiskScoreDict(BaseModel):
    """Individual clause risk score (for API responses)"""
    clause_text: str
    category: str
    severity: float
    severity_level: str
    confidence: float
    risk_explanation: str
    recommended_action: str


class DimensionScoreDict(BaseModel):
    """Dimension risk score (for API responses)"""
    score: float
    severity: str
    weight: Optional[float] = None
    key_findings: List[str]
    problematic_clauses: List[ClauseRiskScoreDict]


class RiskScoreResponse(BaseModel):
    """Response containing risk assessment for a lease agreement"""
    overall_score: float = Field(..., description="Overall risk score (0-100)")
    overall_severity: str = Field(..., description="Overall severity level (Low/Medium/High)")
    financial: DimensionScoreDict = Field(..., description="Financial risk dimension")
    legal_compliance: DimensionScoreDict = Field(..., description="Legal/Compliance risk dimension")
    operational: DimensionScoreDict = Field(..., description="Operational risk dimension")
    timeline: DimensionScoreDict = Field(..., description="Timeline risk dimension")
    strategic_reputational: DimensionScoreDict = Field(..., description="Strategic/Reputational risk dimension (qualitative)")
    top_risks: List[str] = Field(..., description="Top identified risks")
    immediate_actions: List[str] = Field(..., description="Immediate actions to take")
    negotiation_priorities: List[str] = Field(..., description="Priority items for negotiation")
    total_clauses_analyzed: int = Field(..., description="Total number of clauses analyzed")
    high_risk_clauses_count: int = Field(..., description="Number of high-risk clauses")
    timestamp: str = Field(default="", description="ISO timestamp of assessment")


class PDFAnalysisResponse(BaseModel):
    """Response from PDF analysis endpoint"""
    classification_results: str = Field(..., description="Markdown-formatted classification results")
    analysis_results: str = Field(..., description="Markdown-formatted analysis results")
    pages_processed: int = Field(..., description="Number of pages processed from PDF")
    total_characters: int = Field(..., description="Total characters extracted from PDF")
    source_document: str = Field(..., description="Original filename")
    stored_in_kb: bool = Field(..., description="Whether pages were stored in knowledge base")
    total_kb_count: int = Field(..., description="Total documents/pages in knowledge base after this upload")
    risk_assessment: Optional[RiskScoreResponse] = Field(None, description="Optional risk assessment (if enabled)")


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

