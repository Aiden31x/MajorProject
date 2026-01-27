"""
Negotiation Endpoints
Provides AI-powered lease clause negotiation with 3-round controlled process
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.requests import NegotiationRequest
from app.models.responses import NegotiationResponse
from app.services.negotiator import NegotiationAgent
from app.config import GROQ_API_KEY

router = APIRouter(prefix="/api/negotiation", tags=["Negotiation"])


@router.post("/negotiate", response_model=NegotiationResponse)
async def negotiate_clause(request: NegotiationRequest):
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

        # Execute 3-round negotiation
        timestamp = datetime.now().isoformat()
        result = agent.negotiate_clause(
            clause_text=request.clause_text,
            clause_label=request.clause_label,
            risk_score=request.risk_score,
            risk_explanation=request.risk_explanation,
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
