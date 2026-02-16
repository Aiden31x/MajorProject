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


class NegotiationRoundResponse(BaseModel):
    """Single round of negotiation (API response)"""
    round_number: int = Field(..., description="Round number (0=ideal, 1=alternative, 2=fallback)")
    counter_clause: str = Field(..., description="Proposed revised clause")
    justification: str = Field(..., description="Why this change protects tenant interests")
    risk_reduction: float = Field(..., description="Estimated risk reduction percentage (0-100)")
    rejection_text: Optional[str] = Field(None, description="Static rejection text (None for round 0)")
    validation_result: Optional[Dict[str, Any]] = Field(None, description="Validation result for counter-clause")


class NegotiationResponse(BaseModel):
    """Complete 3-round negotiation result (API response)"""
    clause_text: str = Field(..., description="Original risky clause")
    clause_label: str = Field(..., description="Clause category/type")
    risk_score: float = Field(..., description="Original risk score (0-100)")
    risk_explanation: str = Field(..., description="Why this clause is risky")
    stance: str = Field(..., description="Auto-determined negotiation stance (Defensive/Balanced/Soft)")
    rounds: List[NegotiationRoundResponse] = Field(..., description="All 3 negotiation rounds")
    timestamp: str = Field(..., description="ISO timestamp of negotiation")


# Validation Response Models

class ValidationIssueResponse(BaseModel):
    """Single validation issue"""
    issue_type: str = Field(..., description="Type of issue (completeness, contradiction, dangerous_pattern, vague_language, policy_violation)")
    severity: str = Field(..., description="Severity level (critical, major, minor)")
    description: str = Field(..., description="Detailed description of the issue")
    location_hint: str = Field(..., description="Specific part of clause where issue occurs")


class ValidationResponse(BaseModel):
    """Single clause validation result"""
    clause_text: str = Field(..., description="Text of the validated clause")
    status: str = Field(..., description="Validation status (PASS, WARN, FAIL)")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    issues: List[ValidationIssueResponse] = Field(..., description="List of validation issues found")
    timestamp: str = Field(..., description="ISO timestamp of validation")
    validation_time_ms: float = Field(..., description="Time taken for validation in milliseconds")


class BatchValidationResponse(BaseModel):
    """Response for batch validation"""
    results: List[ValidationResponse] = Field(..., description="List of validation results")
    total_validated: int = Field(..., description="Total number of clauses validated")
    passed_count: int = Field(..., description="Number of clauses that passed")
    warned_count: int = Field(..., description="Number of clauses with warnings")
    failed_count: int = Field(..., description="Number of clauses that failed")
    total_time_ms: float = Field(..., description="Total validation time in milliseconds")


class FeedbackSubmitResponse(BaseModel):
    """Response for feedback submission"""
    feedback_id: str = Field(..., description="ID of the created feedback record")
    message: str = Field(..., description="Success message")


class FeedbackAnalyticsResponse(BaseModel):
    """Analytics summary for feedback"""
    total_feedback: int = Field(..., description="Total feedback submissions")
    thumbs_up_count: int = Field(..., description="Number of positive feedback")
    thumbs_down_count: int = Field(..., description="Number of negative feedback")
    top_issues: Dict[str, int] = Field(..., description="Top issues by count")
    accuracy_by_decision: Dict[str, float] = Field(..., description="Accuracy metrics by agent decision")


