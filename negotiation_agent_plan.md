Claude’s Plan
Implementation Plan: Negotiation Agent
Overview
Implement a 3-round negotiation agent for risky lease clauses using Groq API. This is a controlled, demo-friendly system that executes exactly 3 rounds (ideal → alternative → fallback) with static rejection text between rounds.

Architecture Pattern
Following the existing RiskScoringAgent pattern:

Class-based agent with dataclass response models
Retry logic with temperature adjustment (0.3 → 0.1)
Structured JSON outputs via Groq API
FastAPI endpoint with Pydantic request/response models
Core Requirements
3 Fixed Rounds (NOT a chat system):

Round 0: Ideal proposal
Round 1: Alternative after static rejection
Round 2: Fallback after second static rejection
Auto-Determined Stance based on risk_score:

risk_score ≥ 70 → "Defensive"
40 ≤ risk_score < 70 → "Balanced"
risk_score < 40 → "Soft"
Static Rejection Text (NOT LLM-generated):

After Round 0: "The counterparty cannot accept this change due to internal policy."
After Round 1: "The counterparty insists on keeping the original clause."
One LLM Call per Round:

Using Groq API (NOT Gemini)
Strict JSON response format
Max 1 retry per round
No Complexity:

No database storage
No conversation memory
No RAG integration
No emotion simulation
Files to Create/Modify
1. Create /backend/app/services/negotiator.py [NEW - ~250-350 lines]
Dataclasses:


@dataclass
class NegotiationRound:
    round_number: int  # 0, 1, 2
    counter_clause: str
    justification: str
    risk_reduction: float  # 0-100 (numeric score, consistent with RiskScoringAgent)
    rejection_text: Optional[str]  # None for round 0

@dataclass
class NegotiationResult:
    clause_text: str
    clause_label: str
    risk_score: float
    risk_explanation: str
    stance: str  # "Defensive", "Balanced", "Soft"
    rounds: list[NegotiationRound]  # All 3 rounds
    timestamp: str
Class Structure:


class NegotiationAgent:
    ROUND_TYPES = {0: "ideal", 1: "alternative", 2: "fallback"}

    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        """Initialize Groq client"""
        self.client = Groq(api_key=groq_api_key)
        self.model = model

    def _determine_stance(self, risk_score: float) -> str:
        """Return "Defensive", "Balanced", or "Soft" based on risk_score

        Uses explicit if-elif-else logic for clarity and safety:
        - risk_score >= 70 → "Defensive"
        - risk_score >= 40 → "Balanced"
        - risk_score < 40 → "Soft"
        """
        if risk_score >= 70:
            return "Defensive"
        elif risk_score >= 40:
            return "Balanced"
        else:
            return "Soft"

    def _build_round_prompt(
        self, round_number, stance, clause_text, clause_label,
        risk_score, risk_explanation, previous_round
    ) -> str:
        """Build LLM prompt with:
        - Stance-specific instructions (aggressive for Defensive, balanced for Balanced, collaborative for Soft)
        - Round-specific context (ideal vs alternative vs fallback)
        - Previous round results (for rounds 1-2)
        - Risk reduction targets based on stance and round
        - Strict JSON format requirements
        """

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate JSON response - KEEP IT SIMPLE.
        - Try direct JSON parsing first
        - ONE fallback: Extract JSON between first '{' and last '}'
        - Validate required fields: counter_clause, justification, risk_reduction
        - Validate types and ranges (risk_reduction: 0-100 float)
        - Truncate if needed (counter_clause: 2000 chars, justification: 200 chars)
        - If both fail, fail fast - this is a demo system
        """

    def _call_groq_with_retry(self, prompt: str, max_retries: int = 1) -> Dict:
        """Call Groq API with simple retry:
        - Attempt 1: temperature=0.3
        - Attempt 2 (on failure): temperature=0.1 (more deterministic)
        - Use response_format={"type": "json_object"} to force JSON mode
        - Parse and validate response
        - If both attempts fail, raise exception with clear error message
        """

    def _execute_round(
        self, round_number, stance, clause_text, clause_label,
        risk_score, risk_explanation, round0_result, round1_result
    ) -> NegotiationRound:
        """Execute single round:
        - Build prompt with context from previous rounds
        - Call Groq with retry
        - Add static rejection_text (None for round 0, static strings for rounds 1-2)
        - Return NegotiationRound
        """

    def negotiate_clause(
        self, clause_text, clause_label, risk_score,
        risk_explanation, timestamp
    ) -> NegotiationResult:
        """Main entry point:
        1. Determine stance from risk_score
        2. Execute Round 0 (ideal)
        3. Execute Round 1 (alternative) with round0 context
        4. Execute Round 2 (fallback) with round0 + round1 context
        5. Return NegotiationResult with all 3 rounds
        """

    @staticmethod
    def to_dict(negotiation_result: NegotiationResult) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return asdict(negotiation_result)
Static Constants:


REJECTION_TEMPLATES = {
    1: "The counterparty cannot accept this change due to internal policy.",
    2: "The counterparty insists on keeping the original clause."
}
Key Implementation Details:

Stance-Specific Instructions in prompts:

Defensive: "Prioritize tenant safety and fairness. Push for significant changes. Aim for max risk reduction (80-100% ideal, 60-80% alternative, 40-60% fallback)."
Balanced: "Seek fair compromises. Propose reasonable modifications. Aim for moderate risk reduction (60-80% ideal, 40-60% alternative, 30-50% fallback)."
Soft: "Maintain good relations. Propose minor modifications. Aim for modest risk reduction (40-60% ideal, 30-40% alternative, 20-30% fallback)."
Round-Specific Context in prompts:

Round 0: "This is your FIRST and BEST attempt. Propose your ideal solution."
Round 1: "Your ideal was rejected. Previous proposal: {details}. Now propose an ALTERNATIVE approach that's less aggressive but still meaningful."
Round 2: "Both proposals rejected. Previous attempts: Round 0: {details}, Round 1: {details}. This is your FINAL attempt. Make minimal but important changes."
Groq API Call with JSON mode:


response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": "You are a precise legal negotiation expert. Always return valid JSON."},
        {"role": "user", "content": prompt}
    ],
    temperature=temperature,  # 0.3 first, 0.1 on retry
    max_tokens=1024,
    response_format={"type": "json_object"}  # Force JSON mode
)
2. Modify /backend/app/models/responses.py [ADD ~25 lines]
Add at the end of file:


class NegotiationRoundResponse(BaseModel):
    """Single round of negotiation (API response)"""
    round_number: int = Field(..., description="Round number (0=ideal, 1=alternative, 2=fallback)")
    counter_clause: str = Field(..., description="Proposed revised clause")
    justification: str = Field(..., description="Why this change protects tenant interests")
    risk_reduction: float = Field(..., description="Estimated risk reduction percentage (0-100)")
    rejection_text: Optional[str] = Field(None, description="Static rejection text (None for round 0)")


class NegotiationResponse(BaseModel):
    """Complete 3-round negotiation result (API response)"""
    clause_text: str = Field(..., description="Original risky clause")
    clause_label: str = Field(..., description="Clause category/type")
    risk_score: float = Field(..., description="Original risk score (0-100)")
    risk_explanation: str = Field(..., description="Why this clause is risky")
    stance: str = Field(..., description="Auto-determined negotiation stance (Defensive/Balanced/Soft)")
    rounds: List[NegotiationRoundResponse] = Field(..., description="All 3 negotiation rounds")
    timestamp: str = Field(..., description="ISO timestamp of negotiation")
3. Modify /backend/app/models/requests.py [ADD ~10 lines]
Add at the end of file:


class NegotiationRequest(BaseModel):
    """Request to negotiate a risky lease clause"""
    clause_text: str = Field(..., description="Original risky clause text", min_length=10)
    clause_label: str = Field(..., description="Clause category/type (e.g., 'financial', 'termination')")
    risk_score: float = Field(..., description="Risk score (0-100)", ge=0, le=100)
    risk_explanation: str = Field(..., description="Why this clause is risky", min_length=10)
4. Create /backend/app/api/routes/negotiation.py [NEW - ~70 lines]

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
5. Modify /backend/app/config.py [ADD ~5 lines]
Add after existing Gemini configuration (around line 16):


# ================================================================
# Groq API Configuration (for Negotiation Agent)
# ================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
Note: GROQ_API_KEY is already in .env.example, so just needs to be loaded in config.

6. Modify /backend/app/main.py [ADD 2 lines]
Add import (update existing import line around line 10):


from app.api.routes import pdf, chat, kb, document, negotiation  # Add negotiation
Add router registration (after existing routers around line 50):


app.include_router(negotiation.router)
7. Modify /backend/requirements.txt [ADD 1 line]
Add after existing dependencies:


groq>=0.4.0
Prompt Engineering Strategy
Prompt Structure
Each round's prompt consists of:

Role Definition: "You are an expert lease negotiation attorney specializing in tenant representation."
Stance Instructions: Specific for Defensive/Balanced/Soft with risk reduction targets
Context Block: Original clause + round-specific instructions + previous round results
Output Format: Strict JSON schema with explicit "no markdown" instruction
Risk Reduction Targets by Stance
Stance	Round 0 (Ideal)	Round 1 (Alternative)	Round 2 (Fallback)
Defensive (≥70)	80-100%	60-80%	40-60%
Balanced (40-69)	60-80%	40-60%	30-50%
Soft (<40)	40-60%	30-40%	20-30%
JSON Output Format (Consistent with RiskScoringAgent)

{
  "counter_clause": "Complete revised clause text (max 2000 chars)",
  "justification": "Brief explanation (max 200 chars)",
  "risk_reduction": 75.0
}
IMPORTANT: risk_reduction is a numeric float (0-100), NOT "High | Medium | Low". This matches the existing RiskScoringAgent pattern and makes it easy to show decreasing trends across rounds (e.g., 85 → 65 → 45).

Error Handling
1. API Key Validation
Check at endpoint level before agent initialization
Return 400 error with clear message if missing/invalid
2. LLM Call Retry Logic
Attempt 1: temperature=0.3 (balanced creativity)
Attempt 2: temperature=0.1 (deterministic)
Max retries: 1 per round (2 total attempts)
Raise exception with detailed error if both fail
3. JSON Parsing Fallback

try:
    data = json.loads(response_text)
except json.JSONDecodeError:
    # Extract JSON from markdown wrappers like ```json...```
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    json_str = response_text[start_idx:end_idx + 1]
    data = json.loads(json_str)
4. Field Validation
Check required fields exist
Validate types (str, float) and ranges (risk_reduction: 0-100)
Truncate if exceeds limits
Raise ValueError with specific field name if validation fails
5. Route-Level Error Handling
ValueError → 400 (client error)
Exception → 500 (server error)
Include error message in detail field
Testing Strategy
Manual Testing Scenarios
Scenario 1: High-Risk Clause (Defensive - risk_score=85)


{
  "clause_text": "Tenant shall indemnify Landlord against all claims, including legal fees, arising from any incident on the premises, regardless of Landlord's negligence.",
  "clause_label": "legal_compliance",
  "risk_score": 85,
  "risk_explanation": "One-sided liability allocation; tenant liable even for landlord's negligence."
}
Expected: Defensive stance, aggressive changes in Round 0 (mutual indemnification), softened in Rounds 1-2.

Scenario 2: Medium-Risk Clause (Balanced - risk_score=55)


{
  "clause_text": "Rent shall increase by 5% annually, compounded.",
  "clause_label": "financial",
  "risk_score": 55,
  "risk_explanation": "Above-market rent escalation with compounding."
}
Expected: Balanced stance, reasonable changes (3% cap or CPI-based in Round 0).

Scenario 3: Low-Risk Clause (Soft - risk_score=35)


{
  "clause_text": "Tenant must provide 90 days' notice for lease termination.",
  "clause_label": "timeline",
  "risk_score": 35,
  "risk_explanation": "Notice period slightly longer than market standard (60 days)."
}
Expected: Soft stance, minor changes (60 days in Round 0, 75 days in Round 2).

Testing Commands
1. Health Check:


curl http://localhost:8000/api/negotiation/health
2. Full Negotiation:


curl -X POST http://localhost:8000/api/negotiation/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "clause_text": "Tenant shall be solely responsible for all repairs and maintenance, including structural repairs, regardless of cause.",
    "clause_label": "operational",
    "risk_score": 78,
    "risk_explanation": "Unfair maintenance burden; tenant liable for structural repairs typically landlord responsibility."
  }'
3. API Docs:

Visit http://localhost:8000/docs
Find /api/negotiation/negotiate under "Negotiation" tag
Use interactive UI to test with different inputs
Verification
1. Environment Setup

# Add to .env
echo "GROQ_API_KEY=your_actual_groq_key_here" >> backend/.env

# Install dependencies
cd backend
pip install -r requirements.txt

# Verify Groq API key
python -c "from groq import Groq; import os; from dotenv import load_dotenv; load_dotenv(); Groq(api_key=os.getenv('GROQ_API_KEY')).chat.completions.create(model='llama-3.3-70b-versatile', messages=[{'role':'user','content':'test'}], max_tokens=10); print('✅ Groq API key valid')"
2. Backend Startup

cd backend
uvicorn app.main:app --reload --port 8000
Expected logs:


🏢 ClauseCraft FastAPI Backend
📦 Initializing RAG system...
✅ RAG system initialized successfully!
INFO:     Application startup complete.
3. Verify Router Registration
Visit http://localhost:8000/docs
Check for /api/negotiation/negotiate endpoint under "Negotiation" tag
Check for /api/negotiation/health endpoint
4. Health Check

curl http://localhost:8000/api/negotiation/health
Expected: {"status": "healthy", "service": "Negotiation Agent", ...}

5. Full End-to-End Test
Run the manual testing scenario 1 (high-risk clause) and verify:

Response status: 200
Response contains: clause_text, stance: "Defensive", rounds array with 3 items
Round 0 has rejection_text: null
Rounds 1-2 have static rejection text
Each round has counter_clause, justification, risk_reduction
Risk reduction values decrease across rounds (e.g., 85 → 70 → 50)
6. Error Handling Test
Test with missing API key:


# Remove GROQ_API_KEY from .env temporarily
curl -X POST http://localhost:8000/api/negotiation/negotiate \
  -H "Content-Type: application/json" \
  -d '{"clause_text": "test", "clause_label": "test", "risk_score": 50, "risk_explanation": "test"}'
Expected: 400 error with message about missing API key.

Integration with Existing System
Current Flow

PDF Upload → Risk Scorer → Displays risk assessment
Future Flow (Phase 2 - not in this implementation)

PDF Upload → Risk Scorer → Displays risk assessment
                              ↓
                    For high-risk clauses (≥70):
                         "Negotiate" button
                              ↓
                    Negotiation Agent (3 rounds)
                              ↓
                    Display negotiation results
Note: This implementation creates the backend negotiation service. Frontend integration (UI components, API calls from frontend) is out of scope for this task.

Summary
What Gets Implemented
✅ New service: services/negotiator.py (~250-350 lines - KEEP IT SIMPLE)
✅ New API route: api/routes/negotiation.py (~70 lines)
✅ Updated models: models/requests.py (+7 lines), models/responses.py (+25 lines)
✅ Updated config: config.py (+5 lines)
✅ Updated main: main.py (+2 lines)
✅ Updated deps: requirements.txt (+1 line)
What Does NOT Get Implemented
❌ Frontend UI components
❌ Database storage of negotiations
❌ Conversation history/memory
❌ RAG integration
❌ Multi-clause batch negotiation
❌ User feedback loops
Key Constraints
Exactly 3 rounds - no more, no less
Static rejection text - not LLM-generated
One LLM call per round - no additional API calls for validation/refinement
Groq API only - no Gemini for this agent
No state persistence - each negotiation is independent
Estimated Implementation Time
Core service (negotiator.py): 2-3 hours (reduced scope)
API integration (routes, models, config): 1 hour
Testing and refinement: 1 hour
Total: 4-5 hours
Risk Level
Very Low - Pattern is proven (follows RiskScoringAgent), dependencies are stable, scope is intentionally minimal for demo.

⚠️ CRITICAL IMPLEMENTATION RULES
DO:
✅ Keep negotiator.py under 350 lines - if it's getting longer, you're overbuilding
✅ Use risk_reduction: float (0-100) everywhere - NO "High/Medium/Low" strings
✅ Use ONLY server-side GROQ_API_KEY from environment - NO API key in request body
✅ Use explicit if-elif-else for stance determination - clear and safe
✅ Use llama-3.1-8b-instant as default model - faster, cheaper, sufficient quality
✅ Keep JSON parsing simple - one fallback extraction, then fail fast
✅ Exactly 3 rounds, no loops, no chat interface
✅ Static rejection text only - NOT LLM-generated

DON'T:
❌ Accept API keys via request body (security + unnecessary complexity)
❌ Use "High | Medium | Low" for risk_reduction (inconsistent with RiskScoringAgent)
❌ Over-abstract with excessive helper methods
❌ Add complex retry orchestration beyond 2 attempts per round
❌ Use llama-3.3-70b-versatile (overkill for free-tier demo)
❌ Add regex-heavy JSON parsing fallbacks
❌ Make it a chat system or add conversation loops

IF ASKED IN VIVA:
Q: "Why no API key from frontend?"
A: "We intentionally use server-side keys to avoid exposing credentials. This is a security best practice."

Q: "Why only 3 rounds?"
A: "This is a controlled demo system, not a production negotiation platform. 3 rounds balances demonstration value with API cost efficiency."

Q: "Why numeric risk_reduction instead of categories?"
A: "Consistency with our RiskScoringAgent and clearer progression visualization (85 → 65 → 45)."