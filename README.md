# 🏢 ClauseCraft: AI-Powered Lease Agreement Analyzer with RAG

> **Status**: Phase 1 - RAG Foundation Implementation (1-2 weeks)
> **Version**: 2.0 (In Development)
> **Objective**: Transform from basic classifier to grounded legal AI with Retrieval-Augmented Generation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What is ClauseCraft?](#what-is-clausecraft)
3. [Current Architecture](#current-architecture)
4. [RAG System Implementation](#rag-system-implementation)
5. [Installation & Setup](#installation--setup)
6. [Usage](#usage)
7. [Project Structure](#project-structure)
8. [Implementation Timeline](#implementation-timeline)
9. [Testing](#testing)
10. [Future Roadmap](#future-roadmap)
11. [Troubleshooting](#troubleshooting)

---

## Overview

**ClauseCraft** is an AI-powered lease agreement analyzer that uses machine learning for intelligent clause classification and LLM-based analysis. The system is being upgraded to include **RAG (Retrieval-Augmented Generation)** to ground all analysis in evidence from a knowledge base of historical clauses.

### Problem Solved
Currently, the LLM analysis can hallucinate without context. By adding RAG, we enable:
- ✅ **Evidence-Grounded Analysis**: All recommendations cite historical similar clauses
- ✅ **Knowledge Accumulation**: Every processed lease improves future analysis
- ✅ **Risk Pattern Detection**: Identify risky clauses based on historical precedent
- ✅ **Foundation for Agents**: Enable Risk Scoring, Validation, and Negotiation agents

---

## What is ClauseCraft?

### The Problem
Lease agreements are complex legal documents with dozens of clauses covering:
- Rent terms and payment schedules
- Duration, start/end dates
- Lessor and lessee details
- Red flags and problematic terms
- Extensions, VAT, designations of use
- ...and 20+ other clause types

**The Challenge**: Understanding which clauses are risky and what they mean requires legal expertise.

### The Solution
ClauseCraft automates this with:

1. **PDF Ingestion**: Upload any lease agreement
2. **Intelligent Clause Splitting**: Break document into semantic units
3. **ML Classification**: Fine-tuned ALBERT model identifies 26 lease clause types
4. **RAG Grounding**: Retrieve similar historical clauses for context
5. **AI Analysis**: Groq LLM generates grounded, evidence-based insights
6. **Risk Assessment**: Flag problematic clauses with recommendations

---

## Current Architecture

### What Exists (Minor Project Foundation)
```
Input PDF
    ↓
[PDF Extraction] (PyPDF2)
    ↓
[Clause Splitting] (regex)
    ↓
[Classification] (Fine-tuned ALBERT model)
    ↓ Predictions: 26 lease clause types
[LLM Analysis] (Groq - ungrounded)
    ↓
Gradio UI Output
```

### What's Missing (Critical Gaps)
| Component | Status | Impact |
|-----------|--------|--------|
| **Retrieval Subsystem (RAG)** | ❌ Missing | Can't ground analysis in evidence |
| **Clause Knowledge Base** | ❌ Missing | No historical context |
| **Evidence Search** | ❌ Missing | LLM guesses instead of citing sources |
| **Risk Scoring Agent** | ❌ Missing | Can't quantify risk levels |
| **Validator Agent** | ❌ Missing | Can't verify compliance |
| **Rewrite Agent** | ❌ Missing | Can't suggest improvements |

---

## RAG System Implementation

### What is RAG (Retrieval-Augmented Generation)?

RAG combines information retrieval with language generation:

```
User Query (Red Flag Clause)
    ↓
[Vector Database Search]
    ↓ Find similar historical clauses
Retrieved Evidence
    ↓
[Inject into LLM Prompt]
    ↓
Grounded Analysis
```

**Example**:
```
INPUT: "The landlord can increase rent by 50% annually with 30 days notice"

RAG RETRIEVAL: Find 5 similar rent increase clauses from knowledge base
  - Clause 1: "Rent increase limited to 5% annually, 90 days notice" [SAFE]
  - Clause 2: "Unlimited rent increase, 30 days notice" [RISKY]
  - Clause 3: "CPI-linked rent increase capped at 10%" [SAFE]
  ...

LLM ANALYSIS:
  "This clause is HIGH RISK (Score: 8/10). Similar clauses show:
   - Safe practices: CPI-linked, capped increases with 90-day notice
   - Current clause: Unlimited increases with minimal notice
   - Recommendation: Negotiate for 5% annual cap + 90-day notice"
```

### RAG Architecture for ClauseCraft

```
Processed Clauses
    ↓
[Clause Store Manager]
    ├─→ [Embeddings Generator] (sentence-transformers)
    ├─→ [Vector Database] (ChromaDB)
    └─→ [Metadata Storage]

On New Analysis:
    ↓
[Semantic Search]
    ↓ Find top-5 similar clauses
Retrieved Context
    ↓
[Evidence-Enhanced Prompts]
    ↓
[Groq LLM] → Grounded Analysis
```

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- ~2GB free disk space (for models)
- Groq API key (free from [console.groq.com](https://console.groq.com))

### Step 1: Clone & Setup

```bash
cd /Users/aiden/ClauseCraft(Minor)
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

### Step 2: Install Dependencies

```bash
# Install RAG dependencies
pip install chromadb>=0.4.22 sentence-transformers>=2.2.2

# Or install all from requirements.txt
pip install -r requirements.txt
```

**Note**: First time setup downloads ~400MB sentence-transformers model (1-2 minutes).

### Step 3: Verify Installation

```bash
python -c "import chromadb; import sentence_transformers; print('✅ RAG dependencies installed!')"
```

### Step 4: Get Your Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up/Login
3. Create API key
4. Copy to your app (or set in config.py)

---

## Usage

### Running ClauseCraft

```bash
python app.py
```

This launches the Gradio interface at `http://localhost:7860`

### Basic Workflow

1. **Upload PDF**: Click "Upload Lease Agreement (PDF)"
2. **Enter API Key**: Paste your Groq API key (or use default from config)
3. **Click Analyze**: Wait for processing
4. **Review Results**:
   - **Classification Results**: See all identified clauses and their types
   - **AI Analysis**: Read grounded, evidence-based insights with historical context

### What Happens Behind the Scenes

```
1. PDF Extraction (20%)
   └─ Extracts text from your PDF

2. Clause Splitting (30%)
   └─ Splits into individual clauses

3. Classification (40-80%)
   └─ Fine-tuned ALBERT identifies clause types

4. RAG Storage (80%)
   └─ Stores clauses with embeddings in ChromaDB
   └─ Builds knowledge base for future analysis

5. Evidence Retrieval (85%)
   └─ For each red flag, finds similar historical clauses

6. LLM Analysis (90%)
   └─ Groq generates grounded analysis with evidence

7. Results (100%)
   └─ Shows statistics, classifications, and AI insights
```

---

## Project Structure

### Current (Before RAG)
```
ClauseCraft(Minor)/
├── app.py                    # Everything in one file
├── requirements.txt
└── 9epochs-90 (1)/           # Fine-tuned ALBERT model
```

### After RAG Implementation
```
ClauseCraft(Minor)/
├── app.py                    # Gradio UI + main pipeline (REFACTORED)
├── config.py                 # Configuration & constants
├── classifier.py             # LeaseLegalClassifier class
├── pdf_utils.py              # PDF processing functions
├── rag.py                    # ⭐ RAG system - ClauseStore class (CORE)
├── requirements.txt          # Updated dependencies
├── README.md                 # This file
├── chroma_db/                # Vector DB storage (auto-created)
├── 9epochs-90 (1)/           # Fine-tuned ALBERT model
└── venv/                     # Virtual environment
```

### Key Components Explained

#### 1. **config.py** - Central Configuration
```python
# API & Paths
MODEL_PATH = "/Users/aiden/ClauseCraft(Minor)/9epochs-90 (1)"
GROQ_API_KEY = "gsk_..."
CHROMA_DB_PATH = "./chroma_db"

# Classification (26 lease clause types)
LEASE_LABEL_MAP = {
    0: 'expiration_date_of_lease',
    1: 'clause_number',
    2: 'leased_space',
    # ... 23 more
}

# RAG Settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K_SIMILAR_CLAUSES = 5
```

#### 2. **classifier.py** - Clause Classification
```python
class LeaseLegalClassifier:
    """Fine-tuned ALBERT for 26-class lease clause classification."""

    def classify(self, text: str) -> dict:
        """Classify a clause into one of 26 types."""
        return {
            "predicted_label": 5,
            "predicted_class": "lessee",
            "confidence": 0.95
        }

    def classify_batch(self, texts: list) -> list:
        """Batch classify multiple clauses efficiently."""
```

#### 3. **pdf_utils.py** - PDF Processing
```python
def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF files."""

def split_into_clauses(text: str) -> list[str]:
    """Split text into individual clauses using regex."""

def preprocess_clause_text(text: str) -> str:
    """Clean and normalize clause text."""
```

#### 4. **rag.py** - ⭐ THE CORE RAG SYSTEM

This is the heart of the upgrade - the ClauseStore class:

```python
class ClauseStore:
    """Manages clause storage, embeddings, and semantic retrieval."""

    def __init__(self, persist_directory):
        """Initialize ChromaDB + embedding model."""
        self.client = chromadb.PersistentClient(path)
        self.embedding_model = SentenceTransformer(...)
        self.collection = self._get_or_create_collection()

    def add_clause(self, clause_data: dict) -> str:
        """Store single clause with embedding."""
        embedding = self.embedding_model.encode(text)
        self.collection.add(...)
        return clause_id

    def add_clauses_batch(self, clauses: List[dict]) -> List[str]:
        """Batch store clauses for efficiency."""

    def retrieve_similar_clauses(self, query: str, top_k: int = 5):
        """Find top-5 similar clauses using semantic search."""
        query_embedding = self.embedding_model.encode(query)
        results = self.collection.query(embeddings=[query_embedding])
        return similar_clauses

    def get_clauses_by_label(self, label: str) -> List[Dict]:
        """Get all clauses of specific type (e.g., all red flags)."""

    def get_statistics(self) -> Dict:
        """Get total clauses stored, etc."""
```

#### 5. **app.py** - Refactored Gradio UI & Pipeline

Main changes:
- Initialize `ClauseStore` at startup
- After classification, batch store clauses in RAG
- Enhanced LLM prompt with retrieved historical evidence
- UI shows "Stored in Knowledge Base: Yes (X total clauses)"

---

## Implementation Timeline

### Week 1: Foundation

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Refactor app.py → modules | `config.py`, `classifier.py`, `pdf_utils.py` |
| 3-5 | Implement RAG core | `rag.py` with ClauseStore class |
| 6-7 | Integrate RAG into pipeline | Clauses stored after classification |

### Week 2: Grounding & Polish

| Day | Task | Deliverable |
|-----|------|-------------|
| 8-9 | Ground LLM with evidence | `analyze_with_grounded_llm()` function |
| 10-11 | Testing & bug fixes | Pass all test cases |
| 12-13 | Performance optimization | <30s for 50-clause documents |
| 14 | Documentation & final polish | Complete README & deployment guide |

---

## Testing

### Installation Test
```bash
python -c "
from classifier import LeaseLegalClassifier
from rag import ClauseStore
print('✅ All modules imported successfully')
"
```

### Quick Functional Test
```bash
python test_rag.py
```

Expected output:
```
✅ ChromaDB initialized
✅ Clause stored successfully
✅ Retrieval returned 5 similar clauses
✅ All tests passed!
```

### Manual Testing Checklist

- [ ] **Single PDF Processing**
  - Upload lease PDF
  - Verify all clauses classified
  - Check `chroma_db/` directory created
  - Confirm statistics show clauses stored

- [ ] **Persistence Test**
  - Stop and restart `app.py`
  - Verify clause count unchanged
  - Confirm ChromaDB loaded from disk

- [ ] **Retrieval Quality**
  - Manually test with similar queries
  - Verify results are semantically relevant
  - Check confidence scores reasonable

- [ ] **LLM Grounding**
  - Check analysis mentions "similar historical clauses"
  - Verify red flags include context from knowledge base
  - Ensure recommendations cite past examples

- [ ] **Performance**
  - Time a 50-clause document
  - Should complete in <30 seconds
  - Check no memory leaks on restart

- [ ] **Edge Cases**
  - Empty PDF
  - Corrupted PDF
  - Very large PDF (500+ clauses)
  - PDF with no red flags

---

## Tech Stack

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **PDF Processing** | PyPDF2 | Extract text from lease PDFs |
| **Clause Splitting** | Regex | Split text into individual clauses |
| **Classification** | ALBERT (fine-tuned) | Identify 26 lease clause types |
| **Embeddings** | sentence-transformers | Convert clauses to vectors |
| **Vector DB** | ChromaDB | Store & search embeddings |
| **LLM** | Groq (Llama 3.1 8B) | Generate grounded analysis |
| **UI** | Gradio | Web interface |

### Why This Stack?

| Choice | Rationale |
|--------|-----------|
| **Sentence-transformers** (not OpenAI) | Free, local, no API limits, 400MB one-time download |
| **ChromaDB** (not FAISS) | Easier to use, automatic persistence, better metadata handling |
| **Groq** (for LLM) | Fast inference, free tier, no rate limits during testing |
| **Gradio** (not React/Vue) | Simple to update, no frontend complexity, quick prototyping |

---

## Future Roadmap (ClauseCraft 2.0+)

Once RAG foundation is complete, you can build:

### Phase 2: Risk Scoring Agent
```
Input: "Landlord can increase rent 50% with 30 days notice"
    ↓
[Query RAG]: Find similar rent clauses
    ↓
[Risk Analysis]: Compare with industry standards
    ↓
Output: "Risk Score: 8/10 - VERY HIGH"
```

### Phase 3: Validator Agent
```
Input: Processed lease
    ↓
[Query RAG]: Check against regulatory templates
    ↓
[Compliance Check]: Flag violations
    ↓
Output: "⚠️ Clause violates local rent control law"
```

### Phase 4: Rewrite & Negotiation Agent
```
Input: Risky clause + similar safe clauses from RAG
    ↓
[Generate Alternatives]: Create tenant-friendly versions
    ↓
[Justify Changes]: Explain why they're better
    ↓
Output: "SUGGESTED REWRITE: [better clause]"
```

### Phase 5: Feedback Agent
```
User Corrections + RAG Storage
    ↓
[Learn from Feedback]: Improve future analysis
    ↓
[Adaptive Prompts]: Use feedback to refine LLM
```

### Phase 6: Multi-Document Analysis
```
Compare clauses across multiple leases
    ↓
Identify patterns, inconsistencies, deviations
    ↓
Comprehensive comparison report
```

---

## Clauses Supported (26 Types)

ClauseCraft recognizes and classifies:

1. **agreement_type** - Type of lease (residential, commercial, etc.)
2. **annex** - Attached documents/amendments
3. **clause_number** - Numbered references in document
4. **clause_title** - Section headers
5. **definition** - Legal term definitions
6. **definition_number** - Numbered definitions
7. **designated_use** - What the space can be used for
8. **end_date** - Lease expiration date
9. **expiration_date_of_lease** - When lease ends
10. **extension_period** - Options to extend
11. **general_terms** - Standard provisions
12. **indexation_rent** - Rent adjustment formulas
13. **lessee** - Tenant information
14. **lessor** - Landlord information
15. **leased_space** - Property description
16. **notice_period** - Required notice for termination
17. **redflag** - Potentially problematic clause
18. **redflags** - Multiple concerning terms
19. **rent_review_date** - When rent is reviewed
20. **signing_date** - Lease signature date
21. **start_date** - Lease start date
22. **sub_clause_number** - Sub-section numbers
23. **sub_clause_title** - Sub-section headers
24. **term_of_payment** - Payment schedule
25. **type_lease** - Lease classification
26. **vat** - Value-added tax information

---

## Troubleshooting

### Issue: "ChromaDB not found" Error
```python
ModuleNotFoundError: No module named 'chromadb'
```
**Solution**: Install dependencies
```bash
pip install chromadb>=0.4.22 sentence-transformers>=2.2.2
```

### Issue: "Sentence-transformers model download is slow"
```
Loading sentence-transformers/all-MiniLM-L6-v2 (400MB)...
```
**Expected**: First run takes 1-2 minutes to download model. It's cached locally after.

### Issue: "CUDA out of memory" (GPU machines)
**Solution**: Model runs on CPU by default. If you see CUDA errors:
```python
# In rag.py, force CPU
device = torch.device("cpu")
self.embedding_model = SentenceTransformer(model, device="cpu")
```

### Issue: "Groq API rate limit exceeded"
**Solution**: Free tier has limits. During testing, space out requests or use smaller documents.

### Issue: "PDF extraction returns empty text"
**Possible causes**:
- PDF is image-based (scanned document)
- PDF uses special encoding
**Solution**: Convert to text-based PDF first

### Issue: "RAG retrieval returns irrelevant results"
**Cause**: Embedding model may need fine-tuning for legal domain
**Solution**: For Phase 2+, consider fine-tuning sentence-transformers on legal data

---

## Performance Benchmarks

### Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| PDF text extraction | 2-5s | Depends on PDF size |
| Clause splitting | <1s | Regex-based |
| Classification (50 clauses) | 10-15s | ALBERT inference on CPU |
| Embedding generation (50 clauses) | 2-3s | Batch processing |
| ChromaDB storage | <1s | Batch write |
| Semantic search (top-5) | <1s | Vector similarity |
| LLM analysis | 5-10s | Groq inference time |
| **Total (50-clause document)** | **25-35s** | End-to-end |

---

## Contributing & Feedback

This is a semester project with a clear roadmap. For improvements:

1. Document the change
2. Test thoroughly
3. Update README if needed
4. Update plan file if scope changes

---

## License

Educational project - ClauseCraft (Minor) → ClauseCraft 2.0 (Major)

---

## Quick Start Command

```bash
# One-liner to setup and run
cd /Users/aiden/ClauseCraft(Minor) && \
source venv/bin/activate && \
pip install -q chromadb sentence-transformers && \
python app.py
```

---

## References & Resources

### RAG & Vector Databases
- [Chroma Docs](https://docs.trychroma.com/getting-started)
- [Sentence-Transformers](https://www.sbert.net/)
- [RAG Concepts](https://medium.com/@pierrelouislet/getting-started-with-chroma-db-a-beginners-tutorial-6fa32300902)

### Legal AI
- [Clause Classification](https://huggingface.co/tasks/text-classification)
- [NLP for Legal Documents](https://nlp.johnsnowlabs.com/)

### Technologies
- [Groq API](https://groq.com)
- [Gradio](https://gradio.app)
- [ChromaDB](https://trychroma.com)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)

---

**Last Updated**: December 27, 2025
**Current Phase**: 1 - RAG Foundation Design & Planning
**Next Phase**: Implementation (Week 1 Starting Now)

---

> 💡 **Pro Tip**: Your friend's advice was gold - build RAG first, agents later. This creates a solid, evidence-grounded foundation that scales beautifully! 🚀
