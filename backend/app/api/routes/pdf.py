"""
PDF Analysis Endpoints
"""
import os
import tempfile
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from app.models.responses import PDFAnalysisResponse
from app.services.pdf_utils import extract_text_by_pages
from app.services.llm import extract_and_analyze_with_llm
from app.services.rag import ClauseStore
from app.api.deps import get_clause_store

router = APIRouter(prefix="/api/pdf", tags=["PDF Analysis"])


@router.post("/analyze", response_model=PDFAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(..., description="PDF file to analyze"),
    gemini_api_key: str = Form(..., description="Google Gemini API key"),
    clause_store: ClauseStore = Depends(get_clause_store)
):
    """
    Analyze a PDF lease agreement.
    
    Steps:
    1. Validate PDF file
    2. Extract text by pages
    3. Store pages in RAG knowledge base
    4. Use Gemini LLM to extract and classify clauses
    5. Return formatted results
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Validate API key
    if not gemini_api_key or gemini_api_key.strip() == "":
        raise HTTPException(status_code=400, detail="Valid Gemini API key is required")
    
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
        
        # Store pages in RAG system
        timestamp = datetime.now().isoformat()
        source_doc = file.filename
        
        stored_in_kb = False
        total_kb_count = 0
        try:
            clause_store.add_pdf_pages(pages, source_doc, timestamp)
            stored_in_kb = True
            total_kb_count = clause_store.get_statistics()['total_clauses']
        except Exception as e:
            print(f"⚠️ Error storing in RAG: {e}")
            # Continue even if storage fails
        
        # Use Gemini to extract, classify, and analyze
        classification_results, analysis_results = extract_and_analyze_with_llm(
            full_pdf_text,
            source_doc,
            gemini_api_key,
            clause_store
        )
        
        # Return response
        return PDFAnalysisResponse(
            classification_results=classification_results,
            analysis_results=analysis_results,
            pages_processed=len(pages),
            total_characters=len(full_pdf_text),
            source_document=source_doc,
            stored_in_kb=stored_in_kb,
            total_kb_count=total_kb_count
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
