# Risk Scoring Agent Implementation Plan

## Overview
Add a sophisticated risk scoring agent to ClauseCraft that provides both granular (0-100 numerical scores) and categorical (Low/Medium/High) risk assessments across 5 dimensions: Financial, Legal/Compliance, Operational, Timeline, and Strategic/Reputational.

## User Requirements
- **Risk Granularity**: Both numerical (0-100) and categorical (Low/Medium/High)
- **Integration**: Use Gemini LLM directly (not ALBERT classifier)
- **Risk Dimensions**: 5 dimensions with weighted aggregation (4 quantitative + 1 qualitative)
  - Financial risk (35% weight)
  - Legal/compliance risk (30% weight)
  - Operational risk (20% weight)
  - Timeline risk (15% weight)
  - Strategic/Reputational risk (qualitative-only, not included in overall score calculation)
- **Storage**: Store risk scores in ChromaDB for historical analysis
- **Aggregation**: Weighted overall score with severity per clause and confidence scores

## Architecture Integration
The risk scoring agent integrates seamlessly with the existing ClauseCraft architecture:
- **Current Flow**: PDF Upload → Extract Text → Store in RAG → Gemini Classification (Step 1) → Gemini Analysis (Step 2)
- **New Flow**: PDF Upload → Extract Text → Store in RAG → Gemini Classification (Step 1) → Gemini Analysis (Step 2) → **Risk Scoring (Step 3)** → Enhanced Response

---

## Implementation Steps

### 1. Backend: Risk Scoring Service

**File**: `/backend/app/services/risk_scorer.py` (NEW)

Create a new `RiskScoringAgent` class with:

**Data Models** (using dataclasses):
- `ClauseRiskScore`: Individual clause risk with severity, confidence, explanation, recommended action
- `DimensionScore`: Risk score for one dimension (score, severity level, key findings, problematic clauses)
- `RiskAssessment`: Complete assessment with overall score, 5 dimensional scores, top risks, immediate actions, negotiation priorities

**Key Features**:
- Single optimized LLM call for all 5 dimensions (structured JSON output with strict schema)
- Weighted aggregation: `Overall = 0.35×Financial + 0.30×Legal + 0.20×Operational + 0.15×Timeline` (Strategic is qualitative-only, shown separately)
- Severity thresholds: Low (0-39), Medium (40-69), High (70-100) - **non-overlapping for determinism**
- Uses historical context from RAG for risk calibration
- Temperature 0.3 for consistent scoring (falls back to 0.1 if JSON parsing fails)
- Comprehensive scoring rubrics (0-30, 31-60, 61-100) for each dimension
- **Robust error handling**: Retry mechanism with lower temperature (0.1) if JSON parsing fails on first attempt
- **Strict JSON schema enforcement**: Dimension-by-dimension nested structure to prevent blurred boundaries

**Prompt Engineering**:
- Detailed scoring criteria for each of the 5 dimensions
- Financial: Payment terms, hidden costs, rent escalation (>5% = high risk), deposits
- Legal: Liability allocation, tenant protections, compliance, indemnification, insurance
- Operational: Use restrictions, maintenance burden, access rights, assignment/sublease terms
- Timeline: Notice periods, auto-renewal (>1 year = risk), break clauses, flexibility
- Strategic/Reputational: Brand usage, confidentiality asymmetry, non-disparagement, publicity (qualitative insights only)
- Structured JSON output format with dimensional scores, problematic clauses, and recommendations

**JSON Parsing Safeguards**:
- **Strict Schema Example**: Provide explicit JSON structure in prompt with dimension-by-dimension nesting to prevent boundary blur
- **First Attempt**: Temperature 0.3 for balanced consistency and nuance
- **Retry Logic**: If JSON parsing fails, retry same prompt with temperature 0.1 for more deterministic output
- **Fallback**: If both attempts fail, return safe default structure with "Analysis incomplete" flags
- **Validation**: Check that all required fields exist and scores are in valid ranges (0-100)

---

### 2. Backend: LLM Service Update

**File**: `/backend/app/services/llm.py` (MODIFY)

**Add new function**: `extract_analyze_and_score_risks()`
- Orchestrates 3-step pipeline: Classification → Analysis → Risk Scoring
- Calls existing `extract_and_analyze_with_llm()` for steps 1-2
- Instantiates `RiskScoringAgent` and calls `score_lease_agreement()`
- Retrieves historical context from RAG for risk calibration
- Returns tuple: `(classification_results, analysis_results, risk_assessment_dict)`
- Converts risk assessment dataclass to dict for JSON serialization

---

### 3. Backend: RAG System Extension

**File**: `/backend/app/services/rag.py` (MODIFY)

**New method**: `add_pdf_pages_with_risks()`
- Extends existing `add_pdf_pages()` to include risk scores in metadata
- New metadata fields:
  - `overall_risk_score` (float 0-100)
  - `overall_risk_severity` (str: Low/Medium/High)
  - `financial_risk_score`, `legal_risk_score`, `operational_risk_score`, `timeline_risk_score`, `strategic_risk_score` (floats 0-100)
- Enables historical risk pattern detection and trend analysis

**New method**: `get_risk_statistics()`
- Aggregates risk data from knowledge base
- Returns: total documents, average overall risk, high-risk document count, risk distribution (Low/Medium/High counts)
- Useful for dashboard statistics and comparative analysis

---

### 4. Backend: Data Models

**File**: `/backend/app/models/responses.py` (MODIFY)

**New model**: `RiskScoreResponse` (Pydantic)
- Overall score and severity
- 5 dimensional scores (as dicts with score, severity, findings, problematic clauses)
- Aggregated insights: top_risks, immediate_actions, negotiation_priorities
- Metadata: total_clauses_analyzed, high_risk_clauses_count, timestamp

**Extend**: `PDFAnalysisResponse`
- Add optional field: `risk_assessment: Optional[RiskScoreResponse]`
- Maintains backward compatibility (None if risk scoring disabled)

---

### 5. Backend: API Endpoint

**File**: `/backend/app/api/routes/pdf.py` (MODIFY)

**Update**: `/api/pdf/analyze` endpoint
- Add new parameter: `enable_risk_scoring: bool = Form(True)` (default enabled)
- Conditional flow:
  - If `enable_risk_scoring=True`: Call `extract_analyze_and_score_risks()` (3 LLM calls)
  - If `enable_risk_scoring=False`: Call `extract_and_analyze_with_llm()` (2 LLM calls, backward compatible)
- Store pages with risk metadata using `add_pdf_pages_with_risks()` if risk scoring enabled
- Return `PDFAnalysisResponse` with optional `risk_assessment` field populated

---

### 6. Frontend: TypeScript Types

**File**: `/frontend/types/pdf.ts` (MODIFY)

Add new interfaces:
- `ClauseRiskScore`: Individual clause risk assessment
- `DimensionScore`: Single dimension risk score with findings and problematic clauses
- `RiskAssessment`: Complete risk assessment with 5 dimensions and insights

**Extend**: `PDFAnalysisResult`
- Add optional field: `risk_assessment?: RiskAssessment`

---

### 7. Frontend: Risk Visualization Component

**File**: `/frontend/components/pdf/RiskScoreDisplay.tsx` (NEW)

Create comprehensive risk visualization component with:

**Overall Risk Card**:
- Large overall score (0-100) with color-coded severity badge
- Progress bar with dynamic coloring (green/yellow/red)
- Summary stats: Clauses analyzed, high-risk clause count, top risks count
- Color scheme: Green (Low), Yellow (Medium), Red (High)

**Dimensional Breakdown**:
- 5 dimension cards with icons (DollarSign, Scale, Settings, Clock, Shield)
- Each shows: dimension name, weight, score, severity badge, progress bar
- Top 2 key findings per dimension
- Color-coded progress bars based on severity

**Detailed Analysis Tabs**:
1. **Top Risks**: Alert cards showing critical risks with warning icons
2. **Immediate Actions**: Checklist-style action items with checkmark icons
3. **Negotiation Priorities**: Priority items with trending-up icons
4. **Problematic Clauses**: Scrollable list with:
   - Grouped by dimension
   - Clause text excerpt (200 char max)
   - Severity score and badge
   - Category badge
   - Risk explanation
   - Recommended action
   - Confidence percentage

**UI Components**: Uses shadcn/ui (Card, Badge, Progress, Tabs, ScrollArea, Alert)

---

### 8. Frontend: Main Page Integration

**File**: `/frontend/app/page.tsx` (MODIFY)

**Add**:
- State: `const [enableRiskScoring, setEnableRiskScoring] = useState(true)`
- Toggle checkbox in Configuration Card (before Analyze button):
  - Label: "Enable Risk Scoring"
  - Description: "Comprehensive multi-dimensional risk assessment"
  - Disabled during analysis
- Conditional rendering: Display `<RiskScoreDisplay>` if `result?.risk_assessment` exists
- Position: Full-width section before Classification/Analysis results

---

### 9. Frontend: API Client Update

**File**: `/frontend/lib/api/pdf.ts` (MODIFY)

**Update**: `analyzePDF()` function
- Add parameter: `enableRiskScoring: boolean = true`
- Append to FormData: `formData.append('enable_risk_scoring', String(enableRiskScoring))`
- Increase timeout: 300000ms (5 minutes) to accommodate 3 LLM calls

---

### 10. Frontend: Hook Update

**File**: `/frontend/lib/hooks/usePDFAnalysis.ts` (MODIFY)

**Update**: `analyze()` function
- Add parameter: `enableRiskScoring: boolean = true`
- Pass to API: `await analyzePDF(file, apiKey, enableRiskScoring)`

---

### 11. NEW FEATURE: In-Document Clause Highlighting

**Overview**: Create a new interactive document analysis page where users can view the uploaded PDF with risky clauses highlighted, alongside the chat interface for contextual queries.

**Page Layout**: Split-view design
- **Left Panel (60%)**: PDF viewer with clause highlighting
- **Right Panel (40%)**: Chat interface (moved from `/chat` page)

#### 11.1 Backend: Clause Position Extraction

**File**: `/backend/app/services/clause_extractor.py` (NEW)

Create a new service for extracting clause positions within the PDF:

```python
@dataclass
class ClausePosition:
    """Represents a clause's position in the document"""
    clause_text: str
    page_number: int
    start_char: int  # Character position on page
    end_char: int
    risk_score: float
    risk_severity: str
    risk_category: str  # financial, legal, operational, timeline, strategic
    bounding_box: Optional[Dict[str, float]]  # x, y, width, height (if available)

class ClauseExtractor:
    """Extract clause positions from PDF for highlighting"""

    def extract_clauses_with_positions(
        self,
        pdf_pages: List[dict],
        risk_assessment: RiskAssessment
    ) -> List[ClausePosition]:
        """
        Map risky clauses back to their positions in the PDF

        Strategy:
        1. For each problematic clause in risk assessment
        2. Search for clause text in PDF pages
        3. Record page number and character position
        4. Calculate bounding box if possible
        """
        pass

    def fuzzy_match_clause(
        self,
        clause_text: str,
        page_text: str,
        threshold: float = 0.85
    ) -> Optional[Tuple[int, int]]:
        """
        Find clause position using fuzzy string matching
        Returns (start_char, end_char) or None
        """
        pass
```

**Key Challenges**:
- **Text Matching**: Clause text from LLM may not exactly match PDF text (whitespace, line breaks)
- **Solution**: Use fuzzy string matching (difflib, fuzzywuzzy) with 85% threshold
- **Position Accuracy**: Character positions are approximate
- **Solution**: Highlight entire sentences/paragraphs containing the clause

#### 11.2 Backend: New API Endpoint

**File**: `/backend/app/api/routes/document.py` (NEW)

```python
@router.post("/extract-clauses", response_model=ClauseHighlightResponse)
async def extract_clause_positions(
    file: UploadFile = File(...),
    gemini_api_key: Optional[str] = Form(None),
    clause_store: ClauseStore = Depends(get_clause_store)
):
    """
    Extract PDF, analyze risks, and return clause positions for highlighting

    Returns:
        - Full risk assessment
        - Clause positions mapped to pages
        - PDF metadata (total pages, etc.)
    """
    pass

class ClauseHighlightResponse(BaseModel):
    risk_assessment: RiskScoreResponse
    clause_positions: List[ClausePosition]
    pdf_metadata: Dict[str, Any]  # total_pages, file_size, etc.
    pdf_base64: str  # Base64-encoded PDF for frontend rendering
```

**Alternative Approach** (Simpler for MVP):
- Don't extract exact positions initially
- Use page-level highlighting (highlight entire pages containing risky clauses)
- Store clause → page number mapping only
- More precise highlighting can be added in v2

#### 11.3 Frontend: New Document Analysis Page

**File**: `/frontend/app/document/page.tsx` (NEW)

New route: `/document`

**Page Structure**:
```typescript
export default function DocumentAnalysisPage() {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<ClauseHighlightData | null>(null);
  const [selectedClause, setSelectedClause] = useState<ClausePosition | null>(null);

  return (
    <div className="flex h-screen">
      {/* Left Panel: PDF Viewer with Highlighting */}
      <div className="w-3/5 border-r">
        <PDFViewerWithHighlights
          pdfFile={pdfFile}
          clausePositions={analysis?.clause_positions}
          onClauseClick={setSelectedClause}
        />
      </div>

      {/* Right Panel: Chat + Risk Summary */}
      <div className="w-2/5 flex flex-col">
        {/* Risk Summary (Collapsible) */}
        <ClauseRiskSummary
          selectedClause={selectedClause}
          riskAssessment={analysis?.risk_assessment}
        />

        {/* Chat Interface */}
        <div className="flex-1">
          <ChatInterface
            sourceDocument={pdfFile?.name}
            clauseContext={selectedClause}
          />
        </div>
      </div>
    </div>
  );
}
```

#### 11.4 Frontend: PDF Viewer Component

**File**: `/frontend/components/document/PDFViewerWithHighlights.tsx` (NEW)

Use `react-pdf` library for PDF rendering with custom highlighting layer:

```typescript
import { Document, Page } from 'react-pdf';

interface PDFViewerWithHighlightsProps {
  pdfFile: File | null;
  clausePositions?: ClausePosition[];
  onClauseClick: (clause: ClausePosition) => void;
}

export function PDFViewerWithHighlights({
  pdfFile,
  clausePositions,
  onClauseClick
}: PDFViewerWithHighlightsProps) {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);

  // Group clauses by page for efficient rendering
  const clausesByPage = useMemo(() => {
    const grouped: Record<number, ClausePosition[]> = {};
    clausePositions?.forEach(clause => {
      if (!grouped[clause.page_number]) {
        grouped[clause.page_number] = [];
      }
      grouped[clause.page_number].push(clause);
    });
    return grouped;
  }, [clausePositions]);

  const getHighlightColor = (severity: string) => {
    switch (severity) {
      case 'High': return 'rgba(239, 68, 68, 0.3)'; // red
      case 'Medium': return 'rgba(234, 179, 8, 0.3)'; // yellow
      case 'Low': return 'rgba(34, 197, 94, 0.3)'; // green
      default: return 'rgba(156, 163, 175, 0.3)'; // gray
    }
  };

  return (
    <div className="relative h-full overflow-auto">
      <Document file={pdfFile} onLoadSuccess={({ numPages }) => setNumPages(numPages)}>
        <Page pageNumber={pageNumber} renderTextLayer={true}>
          {/* Highlight Layer */}
          <div className="absolute inset-0 pointer-events-none">
            {clausesByPage[pageNumber]?.map((clause, idx) => (
              <div
                key={idx}
                className="absolute cursor-pointer pointer-events-auto"
                style={{
                  top: `${clause.bounding_box?.y || 0}%`,
                  left: `${clause.bounding_box?.x || 0}%`,
                  width: `${clause.bounding_box?.width || 100}%`,
                  height: `${clause.bounding_box?.height || 5}%`,
                  backgroundColor: getHighlightColor(clause.risk_severity),
                  border: `2px solid ${getHighlightColor(clause.risk_severity).replace('0.3', '0.8')}`,
                }}
                onClick={() => onClauseClick(clause)}
                title={`${clause.risk_category} - ${clause.risk_severity} Risk`}
              />
            ))}
          </div>
        </Page>
      </Document>

      {/* Page Navigation */}
      <div className="sticky bottom-0 bg-white border-t p-4 flex items-center justify-between">
        <button onClick={() => setPageNumber(p => Math.max(1, p - 1))}>Previous</button>
        <span>Page {pageNumber} of {numPages}</span>
        <button onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}>Next</button>
      </div>
    </div>
  );
}
```

**Dependencies to Add**:
```bash
npm install react-pdf pdfjs-dist
```

**Simpler MVP Approach** (if exact positioning is too complex):
- Use page-level highlights only (highlight entire page background)
- Show list of risky clauses with "Jump to Page X" buttons
- Clicking clause scrolls to the relevant page
- More precise highlighting added in v2 with better PDF parsing

#### 11.5 Frontend: Clause Risk Summary Component

**File**: `/frontend/components/document/ClauseRiskSummary.tsx` (NEW)

Collapsible panel showing details of selected clause:

```typescript
interface ClauseRiskSummaryProps {
  selectedClause: ClausePosition | null;
  riskAssessment?: RiskAssessment;
}

export function ClauseRiskSummary({ selectedClause, riskAssessment }: ClauseRiskSummaryProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!selectedClause) {
    return (
      <Card className="m-4">
        <CardContent className="pt-6 text-center text-muted-foreground">
          Click on a highlighted clause to see details
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="m-4">
      <CardHeader className="cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Selected Clause Risk</CardTitle>
          <Badge variant={selectedClause.risk_severity === 'High' ? 'destructive' : 'default'}>
            {selectedClause.risk_severity}
          </Badge>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-3">
          <div>
            <span className="font-semibold">Category:</span> {selectedClause.risk_category}
          </div>
          <div>
            <span className="font-semibold">Risk Score:</span> {selectedClause.risk_score.toFixed(1)}
          </div>
          <div>
            <span className="font-semibold">Page:</span> {selectedClause.page_number}
          </div>
          <Separator />
          <div className="text-sm italic text-muted-foreground">
            "{selectedClause.clause_text}"
          </div>
          {/* Show related recommendation from risk assessment */}
        </CardContent>
      )}
    </Card>
  );
}
```

#### 11.6 Frontend: Navigation Update

**File**: `/frontend/components/layout/Navigation.tsx` (NEW or modify existing layout)

Add navigation to switch between:
- `/` - Home/Upload & Analysis
- `/document` - Document Viewer with Highlights (NEW)
- `/chat` - Standalone Chat (keep as is, or deprecate in favor of `/document`)

**Alternative**: Replace `/chat` route with `/document` route entirely (chat is now integrated into document view)

#### 11.7 Implementation Complexity Assessment

**MVP Approach (Recommended for v1)**:
1. **Page-Level Highlighting**: Highlight entire pages that contain risky clauses (simpler)
2. **Clause List View**: Show list of risky clauses with "Jump to Page X" buttons
3. **No Exact Positions**: Skip bounding box calculations initially
4. **Integration**: Reuse existing chat and risk scoring components

**Advantages**:
- Faster implementation
- No complex PDF parsing/position extraction
- Still provides value (users can quickly find risky pages)

**Full Highlighting (v2)**:
- Exact clause position extraction with bounding boxes
- Precise highlighting at sentence/paragraph level
- Requires more sophisticated PDF parsing (potentially PyMuPDF/pdfplumber on backend)

#### 11.8 Updated User Flow

**New Flow**:
1. User uploads PDF on home page (`/`)
2. Backend analyzes and returns risk assessment + clause positions
3. User clicks "View Document with Highlights" button
4. Navigates to `/document` page
5. Left panel: PDF with highlighted risky clauses (color-coded by severity)
6. User clicks highlighted clause → Right panel shows clause details
7. User can ask questions in chat about selected clause or entire document
8. Chat uses RAG context + selected clause for more targeted responses

---

## Dependencies & Setup

### Backend Dependencies (Python)
No new dependencies required for risk scoring (uses existing Gemini SDK).

For in-document highlighting (Phase 2 - precise positioning):
```bash
pip install fuzzywuzzy python-Levenshtein PyMuPDF pdfplumber
```

### Frontend Dependencies (Node.js)
For in-document highlighting (PDF viewer):
```bash
cd frontend
npm install react-pdf pdfjs-dist
```

**react-pdf Configuration**:
- Requires pdfjs-dist worker setup in Next.js
- Add to `next.config.js`:
```javascript
module.exports = {
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
};
```

- Initialize worker in component:
```typescript
import { pdfjs } from 'react-pdf';
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
```

---

## Testing & Verification

### Backend Tests
1. **Unit Tests** (`backend/tests/test_risk_scorer.py`):
   - Test basic risk scoring functionality
   - Test JSON parsing from LLM responses
   - Test weighted score calculation (weights sum to 1.0: 0.35+0.30+0.20+0.15=1.0, Strategic excluded)
   - Test severity level mapping (0-39=Low, 40-69=Medium, 70-100=High - non-overlapping)
   - Test retry mechanism (simulate JSON parsing failure, verify retry with temperature 0.1)
   - Test fallback to safe defaults when both parsing attempts fail

2. **Integration Tests** (`backend/tests/test_pdf_analysis_with_risks.py`):
   - Test complete PDF analysis + risk scoring pipeline
   - Test ChromaDB storage with risk metadata
   - Test backward compatibility (enable_risk_scoring=False)

### Manual Testing Checklist

**Risk Scoring Tests**:
- [ ] Upload PDF with risk scoring enabled → verify complete risk assessment displayed
- [ ] Upload PDF with risk scoring disabled → verify backward compatibility (no risk data)
- [ ] Verify risk scores stored in ChromaDB metadata
- [ ] Check all 5 dimensions display correctly with proper weights
- [ ] Test color coding (green/yellow/red) for Low/Medium/High severity
- [ ] Verify all 4 tabs work (Top Risks, Actions, Negotiation, Problematic Clauses)
- [ ] Test problematic clauses display with recommendations
- [ ] Verify localStorage persistence of risk data
- [ ] Test with high-risk lease → should show High severity
- [ ] Test with low-risk lease → should show Low severity
- [ ] Verify weighted calculation: (0.35×Financial + 0.30×Legal + 0.20×Operational + 0.15×Timeline = 100%, Strategic shown separately as qualitative)
- [ ] Verify severity thresholds: 0-39=Low, 40-69=Medium, 70-100=High (no overlaps)
- [ ] Test JSON parsing retry: Simulate failure, verify retry with lower temperature

**In-Document Highlighting Tests**:
- [ ] Navigate to `/document` page → verify layout (PDF left, chat right)
- [ ] Upload PDF → verify PDF renders correctly in viewer
- [ ] Verify risky clauses are highlighted on PDF (page-level or exact positions)
- [ ] Click highlighted clause → verify right panel shows clause details
- [ ] Verify color coding matches risk severity (red=High, yellow=Medium, green=Low)
- [ ] Test page navigation (Previous/Next buttons)
- [ ] Test "Jump to Page X" functionality for each risky clause
- [ ] Enter chat message → verify RAG context includes selected clause
- [ ] Test chat with no clause selected → verify general document queries work
- [ ] Verify clause positions map correctly to PDF pages
- [ ] Test with multi-page PDF → verify highlights on correct pages
- [ ] Test responsive layout (split-panel resizing if implemented)

### End-to-End Verification

**Risk Scoring Flow**:
1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload sample lease PDF with risk scoring enabled on home page (`/`)
4. Verify 3 LLM calls complete (~45-60 seconds total)
5. Check risk assessment displays with:
   - Overall score and severity badge (Strategic shown separately as qualitative)
   - 4 dimensional breakdowns with correct weights (Financial 35%, Legal 30%, Operational 20%, Timeline 15%)
   - Problematic clauses with recommendations
   - Top risks, actions, and negotiation priorities
6. Check ChromaDB storage: Verify metadata includes risk scores
7. Upload another PDF with risk scoring disabled
8. Verify backward compatibility: No risk assessment section shown

**In-Document Highlighting Flow**:
1. From home page after analysis, click "View Document with Highlights" button (or navigate to `/document`)
2. Upload PDF if not already analyzed
3. Verify split-panel layout:
   - Left panel (60%): PDF viewer with pages rendered
   - Right panel (40%): Clause risk summary + chat interface
4. Verify highlights appear on PDF pages (color-coded: red=High, yellow=Medium, green=Low)
5. Click on highlighted clause:
   - Right panel shows selected clause details
   - Risk category, severity, score displayed
   - Clause text excerpt shown
6. Enter chat query about selected clause:
   - Verify RAG includes clause context in response
   - Verify response is relevant to selected clause
7. Navigate between PDF pages:
   - Verify highlights persist on correct pages
   - Verify page navigation controls work (Previous/Next)
8. Test with multi-page high-risk PDF:
   - Verify highlights distributed across multiple pages
   - Verify "Jump to Page X" functionality works for each risky clause

---

## Critical Files

### Backend (Python)

**Risk Scoring**:
- **NEW**: `/backend/app/services/risk_scorer.py` - Core risk scoring agent (RiskScoringAgent class, 5 dimensional analysis with retry logic)
- **MODIFY**: `/backend/app/services/llm.py` - Add `extract_analyze_and_score_risks()` function
- **MODIFY**: `/backend/app/services/rag.py` - Add `add_pdf_pages_with_risks()` and `get_risk_statistics()` methods
- **MODIFY**: `/backend/app/models/responses.py` - Add `RiskScoreResponse`, extend `PDFAnalysisResponse`
- **MODIFY**: `/backend/app/api/routes/pdf.py` - Update `/api/pdf/analyze` endpoint with `enable_risk_scoring` parameter

**In-Document Highlighting**:
- **NEW**: `/backend/app/services/clause_extractor.py` - Clause position extraction (ClauseExtractor class, fuzzy matching)
- **NEW**: `/backend/app/api/routes/document.py` - New endpoint `/extract-clauses` for clause positions
- **NEW**: `/backend/app/models/document.py` - `ClausePosition`, `ClauseHighlightResponse` models

### Frontend (TypeScript/React)

**Risk Scoring**:
- **NEW**: `/frontend/components/pdf/RiskScoreDisplay.tsx` - Risk visualization component
- **MODIFY**: `/frontend/types/pdf.ts` - Add risk assessment interfaces
- **MODIFY**: `/frontend/app/page.tsx` - Add risk scoring toggle and display integration
- **MODIFY**: `/frontend/lib/api/pdf.ts` - Update `analyzePDF()` with `enableRiskScoring` parameter
- **MODIFY**: `/frontend/lib/hooks/usePDFAnalysis.ts` - Update `analyze()` hook

**In-Document Highlighting**:
- **NEW**: `/frontend/app/document/page.tsx` - New document analysis page (split-panel layout)
- **NEW**: `/frontend/components/document/PDFViewerWithHighlights.tsx` - PDF viewer with highlighting layer
- **NEW**: `/frontend/components/document/ClauseRiskSummary.tsx` - Selected clause details panel
- **NEW**: `/frontend/types/document.ts` - `ClausePosition`, `ClauseHighlightData` interfaces
- **NEW**: `/frontend/lib/api/document.ts` - API client for document analysis endpoints
- **MODIFY**: `/frontend/components/chat/ChatInterface.tsx` - Add `clauseContext` prop for targeted queries
- **MODIFY**: `/frontend/app/layout.tsx` or navigation - Add link to `/document` page

**Dependencies**:
- Add to `package.json`: `react-pdf`, `pdfjs-dist` (for PDF rendering)

---

## Key Technical Decisions

1. **Single LLM Call for All Dimensions**: Efficient approach - Gemini processes all 5 dimensions in one call with structured JSON output (rather than 5 separate calls), with strict schema enforcement to prevent boundary blur

2. **Weighted Scoring (4 Quantitative Dimensions)**: Financial (35%) and Legal (30%) carry most weight, Operational (20%) and Timeline (15%) complete the 100%. Strategic/Reputational is **qualitative-only** (displayed separately, not in overall score calculation)

3. **Non-Overlapping Severity Thresholds**: Low (0-39), Medium (40-69), High (70-100) - ensures deterministic classification with no boundary ambiguity

4. **Retry Mechanism for JSON Parsing**: First attempt uses temperature 0.3 (balanced), if parsing fails retry with temperature 0.1 (more deterministic), fallback to safe defaults if both fail

5. **Structured Prompting**: Detailed scoring rubrics (0-30, 31-60, 61-100) ensure consistent, objective scoring with dimension-by-dimension nested JSON structure

6. **ChromaDB Metadata Storage**: Stores risk scores as metadata (not separate collection), enabling historical analysis without architectural changes

7. **Optional Risk Scoring**: Backward compatible - users can disable for faster 2-step analysis (classification + analysis only)

8. **JSON-First LLM Output**: Structured data format enables programmatic processing, better than markdown parsing

9. **Confidence Scores**: Each clause risk includes confidence (0-1) indicating how explicit/clear the risk is

10. **In-Document Highlighting (MVP)**: Page-level highlighting for simplicity - highlight entire pages containing risky clauses rather than exact positions. Simpler to implement, still provides significant value. Precise highlighting can be added in Phase 2.

---

## Performance Impact

- **Before**: 2 Gemini calls (~30 seconds)
- **After**: 3 Gemini calls (~45-60 seconds)
- **Additional Time**: +15-30 seconds per PDF
- **Mitigation**: Risk scoring is optional (default ON but can be disabled)
- **Storage Impact**: Negligible (~56 bytes per page for 7 float fields)
- **Query Performance**: No impact (metadata is indexed by ChromaDB)

---

## Backward Compatibility

✅ **Guaranteed**:
- Existing PDFs without risk scores continue to work
- Chat/RAG functionality unaffected
- API accepts `enable_risk_scoring=False` for old 2-step behavior
- Frontend gracefully handles missing `risk_assessment` field (displays only classification + analysis)
- ChromaDB queries work for both old and new documents

---

## Implementation Approach Recommendations

### Phase 1 (MVP - Recommended for Initial Release):
1. **Risk Scoring**: Full implementation with 4 quantitative + 1 qualitative dimension
2. **In-Document Highlighting**: Page-level highlighting (simpler)
   - Highlight entire pages containing risky clauses
   - Show list of clauses with "Jump to Page X" buttons
   - No exact bounding box calculations
   - Faster to implement, still provides value

### Phase 2 (Future Enhancements):
1. **Precise Clause Highlighting**: Exact position extraction with bounding boxes
   - Requires more sophisticated PDF parsing (PyMuPDF, pdfplumber)
   - Sentence/paragraph-level highlighting
   - More accurate visual indicators
2. **Risk Trend Analysis**: Track scores over time (multiple documents)
3. **Comparative Risk View**: Compare current lease vs historical averages
4. **Email Alerts**: Notifications for high-risk agreements
5. **Custom Risk Weights**: User-configurable dimension weights (e.g., prioritize financial over timeline)
6. **PDF Export**: Export risk reports with charts as PDF
7. **Advanced Chat**: Multi-turn clause negotiation assistant
8. **Clause Templates**: Suggest alternative clause wording based on risk findings

---

## Summary of Key Fixes & Additions

### Fixes Applied:
1. **Weighting Math**: Strategic/Reputational is now qualitative-only (not in overall score). Overall = 0.35×Financial + 0.30×Legal + 0.20×Operational + 0.15×Timeline = 100% ✅
2. **Severity Thresholds**: Changed from overlapping (0-40, 40-70, 70-100) to non-overlapping (0-39, 40-69, 70-100) for determinism ✅
3. **JSON Parsing Safeguards**: Added retry mechanism with temperature 0.1, strict schema enforcement, fallback to safe defaults ✅

### Major Addition:
4. **In-Document Highlighting**: New `/document` page with split-panel layout (PDF viewer left, chat right), color-coded clause highlighting, and interactive clause selection ✅
