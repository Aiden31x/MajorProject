"""
PDF Analysis Endpoints
"""
import os
import tempfile
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from app.models.responses import PDFAnalysisResponse
from app.services.pdf_utils import extract_text_by_pages
from app.services.llm import extract_and_analyze_with_llm, extract_analyze_and_score_risks
from app.services.rag import ClauseStore
from app.api.deps import get_clause_store
from app.config import GEMINI_API_KEY

router = APIRouter(prefix="/api/pdf", tags=["PDF Analysis"])


@router.post("/analyze", response_model=PDFAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(..., description="PDF file to analyze"),
    gemini_api_key: Optional[str] = Form(None, description="Google Gemini API key (optional, uses server key if not provided)"),
    enable_risk_scoring: bool = Form(True, description="Enable comprehensive risk scoring (default: True)"),
    clause_store: ClauseStore = Depends(get_clause_store)
):
    """
    Analyze a PDF lease agreement.

    Steps:
    1. Validate PDF file
    2. Extract text by pages
    3. Use Gemini LLM to extract and classify clauses
    4. Optionally perform risk scoring (3-step pipeline)
    5. Store pages in RAG knowledge base (with risk metadata if enabled)
    6. Return formatted results

    Note: If gemini_api_key is not provided, the server's configured API key will be used.
    Risk scoring adds ~15-30 seconds to processing time but provides comprehensive analysis.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Use provided API key or fall back to server's configured key
    api_key_to_use = gemini_api_key if gemini_api_key and gemini_api_key.strip() else GEMINI_API_KEY

    # Validate API key
    if not api_key_to_use or api_key_to_use.strip() == "":
        raise HTTPException(status_code=400, detail="Valid Gemini API key is required (either provide one or configure GEMINI_API_KEY in backend .env)")
    
    # Save uploaded file to temporary location
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
            temp_file = temp.name
            content = await file.read()
            temp.write(content)
        
        # Extract text from PDF by pages
        pages = extract_text_by_pages(temp_file)
        
        if not pages or len(pages) == 0:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. Please ensure it's a valid PDF with text content."
            )
        
        # Combine pages into full text for LLM analysis
        full_pdf_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in pages])
        
        if len(full_pdf_text) < 10:
            raise HTTPException(status_code=400, detail="PDF appears to be empty or unreadable")
        
        # Store metadata
        timestamp = datetime.now().isoformat()
        source_doc = file.filename
        
        # Conditional flow: with or without risk scoring
        risk_assessment_dict = None
        
        if enable_risk_scoring:
            print("📊 Risk scoring enabled - using 3-step pipeline")
            # Use 3-step pipeline: Classification → Analysis → Risk Scoring
            classification_results, analysis_results, risk_assessment_dict = extract_analyze_and_score_risks(
                full_pdf_text,
                source_doc,
                api_key_to_use,
                clause_store,
                timestamp
            )
        else:
            print("📊 Risk scoring disabled - using 2-step pipeline")
            # Use 2-step pipeline: Classification → Analysis (backward compatible)
            classification_results, analysis_results = extract_and_analyze_with_llm(
                full_pdf_text,
                source_doc,
                api_key_to_use,
                clause_store
            )
        
        # Store pages in RAG system
        stored_in_kb = False
        total_kb_count = 0
        try:
            if enable_risk_scoring and risk_assessment_dict:
                # Store with risk metadata
                clause_store.add_pdf_pages_with_risks(
                    pages,
                    source_doc,
                    timestamp,
                    risk_assessment_dict
                )
            else:
                # Store without risk metadata (backward compatible)
                clause_store.add_pdf_pages(pages, source_doc, timestamp)
            
            stored_in_kb = True
            total_kb_count = clause_store.get_statistics()['total_clauses']
        except Exception as e:
            print(f"⚠️ Error storing in RAG: {e}")
            # Continue even if storage fails
        
        # Return response
        return PDFAnalysisResponse(
            classification_results=classification_results,
            analysis_results=analysis_results,
            pages_processed=len(pages),
            total_characters=len(full_pdf_text),
            source_document=source_doc,
            stored_in_kb=stored_in_kb,
            total_kb_count=total_kb_count,
            risk_assessment=risk_assessment_dict if enable_risk_scoring else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

