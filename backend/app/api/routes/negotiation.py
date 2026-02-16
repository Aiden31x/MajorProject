"""
Negotiation Endpoints
Provides AI-powered lease clause negotiation with 3-round controlled process
"""
from datetime import datetime
from typing import Optional
import os
from fastapi import APIRouter, HTTPException, Form

from app.models.responses import NegotiationResponse
from app.services.negotiator import NegotiationAgent
from app.services.validator import ValidationAgent, ValidationInput
from app.config import GROQ_API_KEY

router = APIRouter(prefix="/api/negotiation", tags=["Negotiation"])

# Get Gemini API key for validation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


@router.post("/negotiate", response_model=NegotiationResponse)
async def negotiate_clause(
    clause_text: str = Form(..., description="Original risky clause text", min_length=10),
    clause_label: str = Form(..., description="Clause category/type (e.g., 'financial', 'termination')"),
    risk_score: float = Form(..., description="Risk score (0-100)", ge=0, le=100),
    risk_explanation: Optional[str] = Form(None, description="Why this clause is risky"),
    gemini_api_key: Optional[str] = Form(None, description="Optional Gemini API key (ignored, using GROQ)"),
    validate_suggestions: bool = Form(True, description="Whether to validate negotiation rounds"),
):
    """
    Execute 3-round negotiation for a risky lease clause.

    Process:
    1. Auto-determine stance based on risk score (≥70=Defensive, 40-69=Balanced, <40=Soft)
    2. Round 0: Ideal proposal (LLM-generated)
    3. Round 1: Alternative proposal after static rejection
    4. Round 2: Fallback proposal after second static rejection
    5. (Optional) Validate each counter-clause
    6. Return complete negotiation history with all 3 rounds

    Note: NOT a chat system - controlled 3-round process with static rejections.
    Uses server-side GROQ_API_KEY to avoid exposing credentials.
    """
    # Validate API key from environment
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: GROQ_API_KEY not configured in backend .env"
        )

    try:
        # Initialize negotiation agent with server-side API key
        agent = NegotiationAgent(groq_api_key=GROQ_API_KEY)

        # Use a default risk explanation if not provided
        if not risk_explanation:
            risk_explanation = f"This {clause_label} clause has a risk score of {risk_score}/100"

        # Execute 3-round negotiation
        timestamp = datetime.now().isoformat()
        result = agent.negotiate_clause(
            clause_text=clause_text,
            clause_label=clause_label,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            timestamp=timestamp
        )

        # Validate each negotiation round if requested
        if validate_suggestions and GEMINI_API_KEY:
            try:
                validator = ValidationAgent(GEMINI_API_KEY)
                
                for round_obj in result.rounds:
                    validation_result = validator.validate_clause(
                        ValidationInput(
                            clause_text=round_obj.counter_clause,
                            clause_category=clause_label,
                            risk_score=risk_score * (1 - round_obj.risk_reduction / 100),  # Estimated reduced risk
                            risk_explanation=f"Counter-clause for: {risk_explanation}",
                            full_document_context=None
                        )
                    )
                    # Convert to dict and attach to round
                    round_obj.validation_result = validation_result.to_dict()
                    
            except Exception as validation_error:
                # Don't fail negotiation if validation fails
                print(f"Warning: Validation of counter-clauses failed: {validation_error}")

        # Convert to Pydantic response model
        result_dict = NegotiationAgent.to_dict(result)
        return NegotiationResponse(**result_dict)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")


@router.get("/health")
async def negotiation_health():
    """Health check for negotiation service"""
    return {
        "status": "healthy",
        "service": "Negotiation Agent",
        "description": "3-round lease clause negotiation with Groq API"
    }
