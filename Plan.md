# Implementation Plan: Validator & Feedback Agents for ClauseCraft

## Context

ClauseCraft currently performs a 3-step contract analysis pipeline:
1. **Classification** - Categorizes clauses into 26 types
2. **Risk Scoring** - Analyzes clauses across 5 dimensions (financial, legal, operational, timeline, strategic)
3. **Negotiation** - Generates 3 rounds of counter-clause suggestions

**The Gap:** The system provides risk scores and negotiation suggestions but has no mechanism to:
- **Validate** whether a clause is actually acceptable before showing advice to users
- **Learn** whether the advice provided was helpful to users

**The Solution:** Add two new agents with distinct, non-overlapping responsibilities:
- **Validator Agent** - Final checker that determines if a clause is PASS/WARN/FAIL based on completeness, dangerous patterns, contradictions, and vague language
- **Feedback Agent** - Post-interaction learning system that collects user feedback (👍/👎) and converts it to structured tags for future improvement

---

## Architecture Overview

### Validator Agent
- **Service**: New `ValidationAgent` class in `backend/app/services/validator.py`
- **LLM**: Gemini 2.5 Flash (same as RiskScoringAgent for consistency)
- **Output**: PASS/WARN/FAIL status with confidence score and list of issues
- **Trigger Points**:
  1. After risk scoring (automatic for all problematic clauses)
  2. After negotiation (validates counter-clauses)
  3. On-demand (user-triggered button)

### Feedback Agent
- **Service**: New `FeedbackProcessor` class in `backend/app/services/feedback_processor.py`
- **Storage**: PostgreSQL via Prisma (new tables: `ValidationResult`, `Feedback`)
- **UI**: Inline 👍/👎 buttons in `ClauseRiskSummary` and `EditorNegotiationPanel`
- **Tag Conversion**: Server-side logic to convert user selections to structured tags

### Data Flow
```
PDF Upload → Risk Scoring → Validation (NEW) → Display to User
                                                      ↓
                                              User sees advice
                                                      ↓
                                              👍/👎 Feedback (NEW)
                                                      ↓
                                              Store in PostgreSQL
```

---

## Implementation Steps

### Phase 1: Database Schema

**File**: `frontend/prisma/schema.prisma`

Add two new models:

```prisma
model ValidationResult {
  id                String   @id @default(uuid())
  clauseText        String   @db.Text
  clauseCategory    String
  riskScore         Float
  status            String   // PASS, WARN, FAIL
  confidence        Float
  issues            Json     // Array of ValidationIssue objects
  documentSource    String?
  timestamp         DateTime @default(now())
  validationTimeMs  Float?
  feedback          Feedback?

  @@index([status, timestamp])
  @@index([clauseCategory, timestamp])
  @@map("validation_results")
}

model Feedback {
  id                   String           @id @default(uuid())
  validationResultId   String           @unique @map("validation_result_id")
  validationResult     ValidationResult @relation(fields: [validationResultId], references: [id], onDelete: Cascade)
  thumbsUp             Boolean
  followUpReason       String?
  additionalComments   String?          @db.Text
  tags                 Json
  agentDecision        String
  userAcceptedClause   Boolean?
  createdAt            DateTime         @default(now()) @map("created_at")

  @@index([thumbsUp, createdAt])
  @@index([agentDecision, createdAt])
  @@map("feedback")
}
```

**Migration commands**:
```bash
cd frontend
npx prisma migrate dev --name add_validation_and_feedback
npx prisma generate
```

---

### Phase 2: Validator Agent Implementation

**File**: `backend/app/services/validator.py` (NEW)

**Data structures**:
```python
@dataclass
class ValidationIssue:
    issue_type: str  # "completeness", "contradiction", "dangerous_pattern", "vague_language", "policy_violation"
    severity: str    # "critical", "major", "minor"
    description: str
    location_hint: str

@dataclass
class ValidationResult:
    clause_text: str
    status: str      # "PASS", "WARN", "FAIL"
    confidence: float
    issues: List[ValidationIssue]
    timestamp: str
    validation_time_ms: float
```

**Core logic**:
```python
class ValidationAgent:
    def __init__(self, gemini_api_key: str):
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def validate_clause(self, validation_input: ValidationInput) -> ValidationResult:
        """
        Multi-layered validation:
        1. Completeness check (clear parties, obligations, consequences, timeline)
        2. Dangerous patterns (unlimited liability, one-sided terms, unclear termination)
        3. Contradictions (within clause AND across document)
        4. Vague language (ambiguous terms, undefined thresholds)
        5. Policy alignment (against company rules, future feature)

        Temperature: 0.2 (deterministic)
        Response format: JSON with status, confidence, issues array
        """

    def validate_clauses_batch(self, clauses: List[ValidationInput]) -> List[ValidationResult]:
        """Parallel validation using ThreadPoolExecutor for efficiency"""
```

**Status determination logic** (implement with clear comments to avoid edge cases):
```python
# FAIL: Any critical issue with high confidence (≥0.6) OR overall confidence < 0.6
# Reason: Either we're confident something is broken, or we're too uncertain to recommend
if confidence < 0.6 or (confidence >= 0.6 and has_critical_issues):
    status = "FAIL"

# WARN: No critical issues, but one or more major issues
# Reason: Acceptable with caution, user should be aware of concerns
elif has_major_issues and not has_critical_issues:
    status = "WARN"

# PASS: No critical or major issues and high confidence (≥0.8)
# Reason: Safe to proceed, only minor issues at most
else:
    status = "PASS"
```

This avoids:
- FAIL verdicts based on weak evidence
- WARN when something is clearly broken
- PASS when confidence is low even without issues

---

### Phase 3: Validation API Endpoints

**File**: `backend/app/api/routes/validation.py` (NEW)

```python
@router.post("/validate-clause", response_model=ValidationResponse)
async def validate_clause(
    clause_text: str = Form(...),
    clause_category: str = Form(...),
    risk_score: float = Form(...),
    risk_explanation: str = Form(...),
    full_document_text: Optional[str] = Form(None)
):
    """
    Single clause validation on-demand.

    IMPORTANT: Validation uses server-side Gemini API credentials only.
    Do NOT accept API keys from frontend for validation.

    Reason: Validation is a system responsibility, not user-driven inference.
    This ensures consistent validation logic and security.
    """
    # Use server-side GEMINI_API_KEY from environment

@router.post("/validate-batch", response_model=BatchValidationResponse)
async def validate_batch_clauses(...):
    """Batch validation for pipeline integration"""

@router.get("/health")
async def validation_health():
    """Health check"""
```

**Response model** (add to `backend/app/models/responses.py`):
```python
class ValidationIssueResponse(BaseModel):
    issue_type: str
    severity: str
    description: str
    location_hint: str

class ValidationResponse(BaseModel):
    clause_text: str
    status: str
    confidence: float
    issues: List[ValidationIssueResponse]
    timestamp: str
    validation_time_ms: float
```

---

### Phase 4: Pipeline Integration

**File**: `backend/app/services/llm.py` (MODIFY)

Extend `extract_analyze_and_score_risks()` to 4-step pipeline:

```python
def extract_analyze_and_score_risks_with_validation(
    full_pdf_text: str,
    source_doc: str,
    gemini_api_key: str,
    clause_store: ClauseStore,
    timestamp: str,
    enable_validation: bool = True
) -> Tuple[str, str, Dict, List[ValidationResult]]:
    # Steps 1-3: existing code
    classification_results, analysis_results, risk_assessment_dict = extract_analyze_and_score_risks(...)

    # Step 4: Validate high-risk clauses only
    # IMPORTANT: Only validate clauses above risk threshold to keep costs predictable,
    # UI uncluttered, and trust high. Low-risk clauses don't need validation.
    VALIDATION_RISK_THRESHOLD = 40.0  # Only validate Medium (40+) and High (70+) risk clauses

    validation_results = []
    if enable_validation:
        validator = ValidationAgent(gemini_api_key)

        for dimension in ["financial", "legal_compliance", "operational", "timeline", "strategic_reputational"]:
            for clause_dict in risk_assessment_dict[dimension].get("problematic_clauses", []):
                # Skip low-risk clauses (below threshold)
                if clause_dict["severity"] < VALIDATION_RISK_THRESHOLD:
                    continue

                validation_result = validator.validate_clause(
                    ValidationInput(
                        clause_text=clause_dict["clause_text"],
                        clause_category=dimension,
                        risk_score=clause_dict["severity"],
                        risk_explanation=clause_dict["risk_explanation"],
                        full_document_context=full_pdf_text[:50000]
                    )
                )
                validation_results.append(validation_result)
                await store_validation_result(validation_result, source_doc)

    return classification_results, analysis_results, risk_assessment_dict, validation_results
```

**File**: `backend/app/api/routes/document.py` (MODIFY)

Update `/api/document/extract-clauses` to include validation results in response.

**File**: `backend/app/api/routes/negotiation.py` (MODIFY)

Add validation after generating counter-clauses:

```python
@router.post("/negotiate", response_model=NegotiationResponse)
async def negotiate_clause(..., validate_suggestions: bool = Form(True)):
    result = agent.negotiate_clause(...)

    # Validate each negotiation round
    if validate_suggestions and GEMINI_API_KEY:
        validator = ValidationAgent(GEMINI_API_KEY)
        for round_obj in result.rounds:
            validation_result = validator.validate_clause(...)
            round_obj.validation_result = validation_result

    return result
```

Extend `NegotiationRound` dataclass in `backend/app/services/negotiator.py`:
```python
@dataclass
class NegotiationRound:
    # ... existing fields ...
    validation_result: Optional[Dict] = None  # NEW
```

---

### Phase 5: Feedback Service Implementation

**File**: `backend/app/services/feedback_processor.py` (NEW)

```python
@dataclass
class FeedbackData:
    validation_result_id: str
    thumbs_up: bool
    follow_up_reason: Optional[str]
    additional_comments: Optional[str]
    user_accepted_clause: Optional[bool]

class FeedbackProcessor:
    TAG_MAPPING = {
        "too_strict": ["overly_cautious", "false_positive"],
        "too_risky": ["missed_risk", "false_negative"],
        "not_clear": ["explanation_quality", "clarity_issue"],
        "wrong_intent": ["misunderstanding", "context_missing"],
        "other": ["needs_review"]
    }

    def convert_to_tags(self, follow_up_reason: str) -> List[str]:
        """Convert follow-up reason to structured tags"""

    async def store_feedback(self, feedback_data: FeedbackData, prisma_client):
        """Store in PostgreSQL"""
```

---

### Phase 6: Feedback API Endpoints

**File**: `backend/app/api/routes/feedback.py` (NEW)

```python
@router.post("/submit", response_model=FeedbackSubmitResponse)
async def submit_feedback(
    validation_result_id: str = Form(...),
    thumbs_up: bool = Form(...),
    follow_up_reason: Optional[str] = Form(None),
    additional_comments: Optional[str] = Form(None),
    user_accepted_clause: Optional[bool] = Form(None)
):
    """
    Flow:
    1. Lookup validation result
    2. Convert follow_up_reason to tags
    3. Store feedback with relationship
    4. Return feedback_id
    """

@router.get("/analytics", response_model=FeedbackAnalyticsResponse)
async def get_feedback_analytics(time_range: str = Query("7d")):
    """Future: Dashboard analytics"""
```

---

### Phase 7: Frontend Components

**File**: `frontend/components/feedback/ValidationFeedback.tsx` (NEW)

Main feedback component with 👍/👎 buttons:

```tsx
interface ValidationFeedbackProps {
    validationResultId: string;
    validationStatus: 'PASS' | 'WARN' | 'FAIL';
    clauseText: string;
    onFeedbackSubmitted?: () => void;
}

export function ValidationFeedback({ validationResultId, validationStatus, clauseText }: Props) {
    // State: hasVoted, showFollowUp, isSubmitting

    // IMPORTANT: Feedback should never block UX
    // - 👍 feedback: Fire-and-forget (submit immediately, no confirmation)
    // - 👎 follow-up: Optional and dismissible (user can close without answering)
    // This avoids feedback fatigue and annoying users

    // On 👍: Submit immediately with thumbs_up=true, no follow-up
    // On 👎: Show follow-up dialog, but allow dismissal without submission
}
```

**File**: `frontend/components/feedback/FeedbackFollowUpDialog.tsx` (NEW)

Modal with radio options:

```tsx
export function FeedbackFollowUpDialog({ open, onClose, onSubmit }: Props) {
    // Radio options:
    // - Too strict
    // - Too risky
    // - Not clear
    // - Didn't match my intent
    // - Other
    // Optional textarea for additional comments

    // IMPORTANT: Make dismissible
    // - "Skip" or "Close" button to dismiss without submitting
    // - Clicking outside dialog closes it
    // - Escape key closes it
    // User should never feel forced to provide feedback
}
```

**File**: `frontend/components/feedback/ValidationStatusBadge.tsx` (NEW)

Visual indicator for validation status:

```tsx
export function ValidationStatusBadge({ status, confidence }: Props) {
    // PASS: Green badge with checkmark
    // WARN: Yellow/amber badge with warning icon
    // FAIL: Red badge with X icon
    // Show confidence as percentage
}
```

**File**: `frontend/components/feedback/ValidationIssuesList.tsx` (NEW)

Display validation issues:

```tsx
export function ValidationIssuesList({ issues }: Props) {
    // Group by severity (critical → major → minor)
    // Color-coded icons
    // Expandable details
}
```

---

### Phase 8: Frontend Integration

**File**: `frontend/components/document/ClauseRiskSummary.tsx` (MODIFY)

Add validation section after "Recommended Action":

```tsx
{clause.validation_result && (
    <div className="mt-3 space-y-2">
        <ValidationStatusBadge
            status={clause.validation_result.status}
            confidence={clause.validation_result.confidence}
        />

        {clause.validation_result.issues.length > 0 && (
            <ValidationIssuesList issues={clause.validation_result.issues} />
        )}

        <ValidationFeedback
            validationResultId={clause.validation_result.id}
            validationStatus={clause.validation_result.status}
            clauseText={clause.clause_text}
        />
    </div>
)}
```

**File**: `frontend/components/editor/EditorNegotiationPanel.tsx` (MODIFY)

Add validation after each negotiation round:

```tsx
{round.validation_result && (
    <div className="mt-3 p-3 border-t">
        <div className="text-xs font-semibold mb-2">Validation Check:</div>
        <ValidationStatusBadge {...} />
        <ValidationIssuesList {...} />
        <ValidationFeedback {...} />
    </div>
)}
```

---

### Phase 9: Type Definitions

**File**: `frontend/types/validation.ts` (NEW)

```typescript
export interface ValidationIssue {
    issue_type: string;
    severity: 'critical' | 'major' | 'minor';
    description: string;
    location_hint: string;
}

export interface ValidationResult {
    id: string;
    clause_text: string;
    status: 'PASS' | 'WARN' | 'FAIL';
    confidence: number;
    issues: ValidationIssue[];
    timestamp: string;
    validation_time_ms: number;
}

export interface FeedbackSubmission {
    validation_result_id: string;
    thumbs_up: boolean;
    follow_up_reason?: 'too_strict' | 'too_risky' | 'not_clear' | 'wrong_intent' | 'other';
    additional_comments?: string;
    user_accepted_clause?: boolean;
}
```

**File**: `frontend/types/document.ts` (MODIFY)

Extend `ClausePosition`:
```typescript
export interface ClausePosition {
    // ... existing fields ...
    validation_result?: ValidationResult;  // NEW
}
```

**File**: `frontend/types/editor.ts` (MODIFY)

Extend `NegotiationRound`:
```typescript
export interface NegotiationRound {
    // ... existing fields ...
    validation_result?: ValidationResult;  // NEW
}
```

**File**: `frontend/lib/api/validation.ts` (NEW)

```typescript
export async function validateClause(
    clauseText: string,
    clauseCategory: string,
    riskScore: number,
    riskExplanation: string,
    apiKey: string,
    fullDocumentText?: string
): Promise<ValidationResult> { ... }

export async function submitFeedback(feedback: FeedbackSubmission): Promise<string> { ... }
```

---

### Phase 10: Backend Registration

**File**: `backend/app/main.py` (MODIFY)

Register new routers:

```python
from app.api.routes import validation, feedback

app.include_router(validation.router, prefix="/api/validation", tags=["Validation"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
```

---

## Critical Files Summary

### New Files
- `backend/app/services/validator.py` - Validator agent logic
- `backend/app/services/feedback_processor.py` - Feedback processing and tagging
- `backend/app/api/routes/validation.py` - Validation API endpoints
- `backend/app/api/routes/feedback.py` - Feedback API endpoints
- `frontend/components/feedback/ValidationFeedback.tsx` - Main feedback UI component
- `frontend/components/feedback/FeedbackFollowUpDialog.tsx` - Follow-up modal
- `frontend/components/feedback/ValidationStatusBadge.tsx` - Status indicator
- `frontend/components/feedback/ValidationIssuesList.tsx` - Issues display
- `frontend/types/validation.ts` - TypeScript type definitions
- `frontend/lib/api/validation.ts` - API client functions

### Modified Files
- `frontend/prisma/schema.prisma` - Add ValidationResult and Feedback models
- `backend/app/services/llm.py` - Extend pipeline to 4 steps with validation
- `backend/app/services/negotiator.py` - Add validation_result to NegotiationRound
- `backend/app/api/routes/document.py` - Include validation results in response
- `backend/app/api/routes/negotiation.py` - Validate counter-clauses
- `backend/app/models/responses.py` - Add validation response models
- `backend/app/main.py` - Register new routers
- `frontend/components/document/ClauseRiskSummary.tsx` - Add validation section
- `frontend/components/editor/EditorNegotiationPanel.tsx` - Show validation for rounds
- `frontend/types/document.ts` - Extend ClausePosition interface
- `frontend/types/editor.ts` - Extend NegotiationRound interface

---

## Verification Strategy

### Unit Tests

**Backend**:
```bash
backend/tests/test_validator.py
- test_validator_pass_status()
- test_validator_fail_status()
- test_validator_detects_completeness_issues()
- test_validator_detects_contradictions()

backend/tests/test_feedback.py
- test_feedback_tag_conversion()
- test_feedback_storage()
```

**Frontend**:
```bash
frontend/__tests__/ValidationFeedback.test.tsx
- Shows thumbs up/down buttons
- Opens follow-up dialog on thumbs down
- Submits feedback successfully
- Disables buttons after voting
```

### Integration Tests

**End-to-end flows**:
1. Upload PDF → Risk scoring → Automatic validation → Validation results in UI
2. Click 👎 → Submit follow-up → Verify stored in PostgreSQL
3. Negotiate clause → Counter-clauses validated → Validation shown inline
4. Accept suggestion → Track user_accepted_clause=true

### Manual Testing Checklist

- [ ] Upload PDF, verify all clauses validated automatically
- [ ] Check validation badges (PASS=green, WARN=yellow, FAIL=red)
- [ ] Click 👍 on PASS clause, verify feedback stored in DB
- [ ] Click 👎 on FAIL clause, submit follow-up "too_strict", verify tags=["overly_cautious", "false_positive"]
- [ ] Negotiate clause, verify counter-clauses show validation
- [ ] Accept negotiated clause, verify user_accepted_clause=true in database
- [ ] Check PostgreSQL: `SELECT * FROM validation_results;` and `SELECT * FROM feedback;`
- [ ] Performance: Validation adds <5s per clause

---

## Performance Considerations

**Batch Validation**: Use `ThreadPoolExecutor` to validate multiple clauses in parallel (already implemented in RiskScoringAgent pattern)

**Caching**: Cache validation results by clause text hash (24-hour TTL) to avoid redundant LLM calls

**Cost Estimate**:
- Per clause: ~$0.001 (Gemini 2.5 Flash)
- 20-clause document: ~$0.02 total
- Processing time: ~30 seconds for batch validation

---

## Implementation Order

1. **Database** (Phase 1) - Run Prisma migrations first
2. **Validator Agent** (Phases 2-3) - Core validation logic and API
3. **Pipeline Integration** (Phase 4) - Connect to existing flow
4. **Feedback Service** (Phases 5-6) - Feedback processing and API
5. **Frontend Components** (Phases 7-8) - UI for validation and feedback
6. **Type Definitions** (Phase 9) - TypeScript interfaces
7. **Registration** (Phase 10) - Wire everything together
8. **Testing** (Verification) - Ensure quality

---

## Key Design Decisions

- **Validator uses Gemini** (not Groq) for deep reasoning and consistency with RiskScoringAgent
- **Validator uses server-side credentials only** - No client-passed API keys for security and consistency
- **Tri-state status** (PASS/WARN/FAIL) with clear edge-case handling to avoid confusion
- **Only validate high-risk clauses** (threshold: 40+) to keep costs predictable and UI uncluttered
- **Inline feedback** (👍/👎 buttons) that's fire-and-forget and never blocks UX
- **Follow-up questions are optional and dismissible** - No feedback fatigue
- **Server-side tag conversion** ensures consistent categorization
- **PostgreSQL storage** (not ChromaDB) for relational feedback queries
- **Batch processing** for performance optimization
