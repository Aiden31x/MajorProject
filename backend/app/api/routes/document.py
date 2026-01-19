"""
Document Analysis API Routes
Endpoints for extracting clause positions and providing PDF with highlights
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import base64
from datetime import datetime

from app.models.document import (
    ClauseHighlightResponse,
    ClausePositionResponse,
    PDFMetadata
)
from app.services.clause_extractor import ClauseExtractor, ClausePosition
from app.services.pdf_utils import extract_text_from_pdf, extract_text_by_pages
from app.services.llm import extract_analyze_and_score_risks
from app.services.risk_scorer import RiskScoringAgent
from app.config import GEMINI_API_KEY
from app.api.deps import get_clause_store

router = APIRouter(prefix="/api/document", tags=["document"])


@router.post("/extract-clauses", response_model=ClauseHighlightResponse)
async def extract_clause_positions(
    file: UploadFile = File(...),
    gemini_api_key: Optional[str] = Form(None),
    clause_store = Depends(get_clause_store)
):
    """
    Extract PDF, analyze risks, and return clause positions for highlighting
    
    This endpoint:
    1. Extracts text from the uploaded PDF
    2. Performs risk analysis using Gemini LLM
    3. Maps risky clauses to their page positions
    4. Returns the complete analysis with clause positions and PDF data
    
    Args:
        file: PDF file to analyze
        gemini_api_key: Optional Gemini API key (uses env var if not provided)
    
    Returns:
        ClauseHighlightResponse with risk assessment, clause positions, and PDF data
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Get API key
    api_key = gemini_api_key or GEMINI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key required. Provide via form data or GEMINI_API_KEY env var."
        )
    
    try:
        # Read PDF file
        pdf_content = await file.read()
        file_size = len(pdf_content)
        
        # Extract text and pages
        print(f"📄 Extracting text from PDF: {file.filename}")
        
        # Get full text
        full_text = extract_text_from_pdf(pdf_content)
        
        # Get pages (returns [{"page": 1, "text": "..."}, ...])
        pages_data = extract_text_by_pages(pdf_content)
        
        # Convert to format expected by clause extractor (page_number instead of page)
        pdf_pages = [
            {
                "page_number": page["page"],
                "text": page["text"]
            }
            for page in pages_data
        ]
        total_pages = len(pdf_pages)
        
        if not full_text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF")
        
        print(f"✅ Extracted {len(full_text)} characters from {total_pages} pages")
        
        # Perform risk analysis
        print("🤖 Starting risk analysis...")
        timestamp = datetime.utcnow().isoformat()

        # Call the 3-step pipeline (classification, analysis, risk scoring)
        classification_results, analysis_results, risk_assessment_dict = \
            extract_analyze_and_score_risks(
                full_pdf_text=full_text,
                source_doc=file.filename,
                gemini_api_key=api_key,
                clause_store=clause_store,
                timestamp=timestamp,
                pdf_pages=pdf_pages  # NEW: Pass page data for position extraction
            )
        
        print(f"✅ Risk analysis complete: Overall score {risk_assessment_dict['overall_score']}")
        
        # Extract clause positions
        print("🔍 Extracting clause positions...")

        # Debug: Show sample of first page to understand format
        if pdf_pages:
            first_page_sample = pdf_pages[0].get('text', '')[:500]
            print(f"📄 First page sample (500 chars): {first_page_sample}")

        try:
            extractor = ClauseExtractor(fuzzy_threshold=0.60)  # Lowered for better article matching
            clause_positions = extractor.extract_clauses_with_positions(
                pdf_pages,
                risk_assessment_dict
            )

            print(f"✅ Found {len(clause_positions)} clause positions")

            # Log LLM vs fallback usage
            if clause_positions:
                llm_provided = sum(1 for cp in clause_positions if cp.start_char >= 0)
                fallback_count = len(clause_positions) - llm_provided
                print(f"📊 Positions: {llm_provided} from LLM, {fallback_count} from fallback")

        except Exception as e:
            print(f"⚠️ Error extracting positions: {e}")
            # Graceful degradation: Continue with empty positions
            clause_positions = []
        
        # Convert clause positions to response models
        clause_position_responses = [
            ClausePositionResponse(
                clause_text=cp.clause_text,
                page_number=cp.page_number,
                start_char=cp.start_char,
                end_char=cp.end_char,
                risk_score=cp.risk_score,
                risk_severity=cp.risk_severity,
                risk_category=cp.risk_category,
                risk_explanation=cp.risk_explanation,
                recommended_action=cp.recommended_action,
                confidence=cp.confidence,
                bounding_box=cp.bounding_box
            )
            for cp in clause_positions
        ]
        
        # Encode PDF to base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Prepare metadata
        pdf_metadata = PDFMetadata(
            total_pages=total_pages,
            file_size=file_size,
            filename=file.filename
        )
        
        # Return complete response
        return ClauseHighlightResponse(
            risk_assessment=risk_assessment_dict,
            clause_positions=clause_position_responses,
            pdf_metadata=pdf_metadata,
            pdf_base64=pdf_base64
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in clause extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )
