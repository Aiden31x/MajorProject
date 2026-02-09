# Plan: Text-Based Document Editor with Clause Highlighting

## Overview
Add a TipTap-based rich text editor view that displays extracted PDF text with character-level clause highlighting, allowing users to click risky clauses, view negotiation suggestions, and accept rewrites inline.

## Architecture Decision
**Add as a tab alongside existing PDF viewer** (not replace it)
- Users can toggle between "PDF View" (original layout) and "Editor View" (editable text)
- Preserves existing functionality while adding new capabilities

---

## Files to Create

### Backend
| File | Purpose |
|------|---------|
| `backend/app/api/routes/editor.py` | New endpoint `/api/editor/extract-for-editor` |
| `backend/app/models/editor.py` | `EditorDocumentResponse` and `EditorClausePosition` models |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/components/editor/DocumentTextEditor.tsx` | Main TipTap editor with clause highlighting |
| `frontend/components/editor/ClauseHighlightExtension.ts` | Custom TipTap Mark for severity-colored highlights |
| `frontend/components/editor/EditorNegotiationPanel.tsx` | Side panel with "Accept" buttons for suggestions |
| `frontend/types/editor.ts` | TypeScript types for editor state |
| `frontend/lib/api/editor.ts` | API client for editor endpoint |

### Files to Modify
| File | Changes |
|------|---------|
| `frontend/app/document/page.tsx` | Add tabs to switch between PDF/Editor views |
| `frontend/package.json` | Add TipTap dependencies |
| `backend/app/main.py` | Register new editor router |

---

## Implementation Steps

### Phase 1: Backend - New Endpoint

**1. Create `backend/app/models/editor.py`**
```python
class EditorClausePosition(BaseModel):
    id: str  # UUID for React keys
    clause_text: str
    absolute_start: int  # Position in concatenated full text
    absolute_end: int
    page_number: int
    risk_score: float
    risk_severity: str
    risk_category: str
    risk_explanation: str
    recommended_action: str

class EditorDocumentResponse(BaseModel):
    full_text: str  # All pages concatenated
    clause_positions: List[EditorClausePosition]
    page_boundaries: List[int]  # Where each page starts
    risk_assessment: Dict[str, Any]
    pdf_metadata: PDFMetadata
```

**2. Create `backend/app/api/routes/editor.py`**
- New endpoint: `POST /api/editor/extract-for-editor`
  - Accepts PDF file upload
  - Reuses existing `extract_analyze_and_score_risks()` pipeline
  - Concatenates pages with `\n\n` separators
  - Transforms page-relative positions to absolute positions

- New endpoint: `POST /api/editor/reanalyze-text`
  - Accepts raw text (after user edits)
  - Re-runs risk scoring on the modified text
  - Returns updated `clause_positions` with new absolute positions
  - Used after user accepts a rewrite to refresh highlighting

### Phase 2: Frontend - TipTap Setup

**3. Install dependencies**
```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/pm
```

**4. Create `ClauseHighlightExtension.ts`**
- Custom TipTap Mark with attributes: `clauseId`, `severity`, `category`, `explanation`
- Severity-based background colors:
  - High: `rgba(239, 68, 68, 0.3)` (red)
  - Medium: `rgba(234, 179, 8, 0.3)` (yellow)
  - Low: `rgba(34, 197, 94, 0.3)` (green)
- Click handler emits custom event with clause data

**5. Create `DocumentTextEditor.tsx`**
- Receives `fullText` and `clausePositions` props
- On mount: applies highlight marks at each clause position
- Exposes `replaceClauseText(clauseId, newText)` method for accepting suggestions
- Emits `onClauseClick` when user clicks a highlighted clause

### Phase 3: Frontend - Integration

**6. Create `EditorNegotiationPanel.tsx`**
- Shows selected clause details
- "Get Suggestions" button calls existing `/api/negotiation/negotiate`
- Displays 3 rounds of counter-clauses (reuse existing `NegotiationDialog` UI patterns)
- **"Accept" button** on each round → calls `replaceClauseText()` on editor

**7. Create `frontend/types/editor.ts`**
```typescript
interface EditorClausePosition {
  id: string;
  clause_text: string;
  absolute_start: number;
  absolute_end: number;
  page_number: number;
  risk_score: number;
  risk_severity: 'High' | 'Medium' | 'Low';
  risk_category: string;
  risk_explanation: string;
  recommended_action: string;
}
```

**8. Create `frontend/lib/api/editor.ts`**
```typescript
export async function extractForEditor(file: File, apiKey: string): Promise<EditorDocumentResponse>
```

### Phase 4: View Toggle

**9. Modify `frontend/app/document/page.tsx`**
- Add `viewMode` state: `'pdf' | 'editor'`
- Add tabs component at top of analysis view
- Conditionally render `PDFViewerWithHighlights` or `DocumentTextEditor`
- Share `analysis` state between views (analyze once, display in either view)

---

## Data Flow

```
[PDF Upload] → [Analyze Button]
      ↓
[Backend: extract-for-editor]
      ↓
[Returns: full_text + clause_positions with absolute positions]
      ↓
[Frontend: DocumentTextEditor]
      ↓
[TipTap renders text with highlighted marks]
      ↓
[User clicks clause] → [EditorNegotiationPanel shows]
      ↓
[User clicks "Get Suggestions"] → [/api/negotiation/negotiate]
      ↓
[3 rounds displayed with "Accept" buttons]
      ↓
[User clicks "Accept"] → [editor.replaceClauseText()] → [Text updated in editor]
```

---

## Key Technical Details

### Position Mapping (Backend)
```python
# Build page boundaries
page_boundaries = [0]
full_text_parts = []
for page in pdf_pages:
    full_text_parts.append(page['text'])
    page_boundaries.append(page_boundaries[-1] + len(page['text']) + 2)  # +2 for \n\n

full_text = '\n\n'.join(full_text_parts)

# Transform clause positions
for clause in clause_positions:
    page_offset = page_boundaries[clause.page_number - 1]
    absolute_start = page_offset + clause.start_char
    absolute_end = page_offset + clause.end_char
```

### Applying Highlights (Frontend)
```typescript
// Sort descending to apply from end to start (avoids position shifts)
const sorted = [...clauses].sort((a, b) => b.absolute_start - a.absolute_start);

sorted.forEach(clause => {
  editor.chain()
    .setTextSelection({ from: clause.absolute_start + 1, to: clause.absolute_end + 1 })
    .setMark('clauseHighlight', { clauseId: clause.id, severity: clause.risk_severity })
    .run();
});
```

### Replacing Clause Text
```typescript
const replaceClauseText = async (clauseId: string, newText: string) => {
  const clause = clauses.find(c => c.id === clauseId);

  // 1. Replace text in editor
  editor.chain()
    .setTextSelection({ from: clause.absolute_start + 1, to: clause.absolute_end + 1 })
    .insertContent(newText)
    .run();

  // 2. Re-analyze to recalculate all clause positions
  // Get updated text from editor and send to backend for re-analysis
  const updatedText = editor.getText();
  await reanalyzeDocument(updatedText);  // Refreshes clause positions
};
```

---

## Verification Plan

1. **Backend endpoint**
   - Upload a test PDF to `/api/editor/extract-for-editor`
   - Verify response contains `full_text` and `clause_positions` with valid absolute positions
   - Check that `absolute_start` < `absolute_end` for all clauses

2. **Frontend editor**
   - Load extracted text in TipTap
   - Verify clauses are highlighted with correct colors
   - Click a clause → verify `onClauseClick` fires with correct data

3. **Negotiation flow**
   - Click "Get Suggestions" → verify API call succeeds
   - Click "Accept" on a round → verify text is replaced in editor
   - Verify the replaced text is no longer highlighted (mark removed)

4. **View toggle**
   - Analyze a PDF
   - Switch between PDF View and Editor View
   - Verify both views show the same document

---

## Out of Scope (Future)
- DOCX export (can be added later with `python-docx`)
- Position recalculation after edits (start with re-analyze approach)
- Undo/redo for accepted suggestions
