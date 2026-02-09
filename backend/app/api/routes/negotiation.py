"""
Negotiation Endpoints
Provides AI-powered lease clause negotiation with 3-round controlled process
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Form

from app.models.responses import NegotiationResponse
from app.services.negotiator import NegotiationAgent
from app.config import GROQ_API_KEY

router = APIRouter(prefix="/api/negotiation", tags=["Negotiation"])


@router.post("/negotiate", response_model=NegotiationResponse)
async def negotiate_clause(
    clause_text: str = Form(..., description="Original risky clause text", min_length=10),
    clause_label: str = Form(..., description="Clause category/type (e.g., 'financial', 'termination')"),
    risk_score: float = Form(..., description="Risk score (0-100)", ge=0, le=100),
    risk_explanation: Optional[str] = Form(None, description="Why this clause is risky"),
    gemini_api_key: Optional[str] = Form(None, description="Optional Gemini API key (ignored, using GROQ)"),
):
    """
    Execute 3-round negotiation for a risky lease clause.

    Process:
    1. Auto-determine stance based on risk score (≥70=Defensive, 40-69=Balanced, <40=Soft)
    2. Round 0: Ideal proposal (LLM-generated)
    3. Round 1: Alternative proposal after static rejection
    4. Round 2: Fallback proposal after second static rejection
    5. Return complete negotiation history with all 3 rounds

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
