"""
Editor API Routes
Endpoints for TipTap editor view with absolute position tracking
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import base64
import uuid
from datetime import datetime

from app.models.editor import EditorDocumentResponse, EditorClausePosition
from app.models.document import PDFMetadata
from app.services.clause_extractor import ClauseExtractor
from app.services.pdf_utils import extract_text_from_pdf, extract_text_by_pages
from app.services.llm import extract_analyze_and_score_risks
from app.config import GEMINI_API_KEY
from app.api.deps import get_clause_store

router = APIRouter()


@router.post("/extract-for-editor", response_model=EditorDocumentResponse)
async def extract_for_editor(
    file: UploadFile = File(...),
    gemini_api_key: Optional[str] = Form(None),
    clause_store = Depends(get_clause_store)
):
    """
    Extract PDF text and analyze for editor view with absolute positions
    
    This endpoint:
    1. Extracts text from PDF pages
    2. Concatenates pages with \\n\\n separators
    3. Performs risk analysis
    4. Transforms clause positions from page-relative to absolute
    5. Returns data ready for TipTap editor
    
    Args:
        file: PDF file to analyze
        gemini_api_key: Optional Gemini API key
        
    Returns:
        EditorDocumentResponse with full text and absolute clause positions
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
        
        print(f"📄 Extracting text from PDF for editor: {file.filename}")
        
        # Get full text
        full_text = extract_text_from_pdf(pdf_content)
        
        # Get pages
        pages_data = extract_text_by_pages(pdf_content)
        
        # Convert to format expected by clause extractor
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
        
        # Build page boundaries and concatenated text
        page_boundaries = [0]
        full_text_parts = []
        
        for page in pdf_pages:
            page_text = page["text"]
            full_text_parts.append(page_text)
            # Calculate next boundary: current boundary + page length + 2 for \n\n
            page_boundaries.append(page_boundaries[-1] + len(page_text) + 2)
        
        # Concatenate with \n\n separators
        concatenated_text = "\n\n".join(full_text_parts)
        
        print(f"📊 Page boundaries: {page_boundaries[:5]}... (showing first 5)")
        
        # Perform risk analysis
        print("🤖 Starting risk analysis...")
        timestamp = datetime.utcnow().isoformat()
        
        classification_results, analysis_results, risk_assessment_dict = \
            extract_analyze_and_score_risks(
                full_pdf_text=full_text,
                source_doc=file.filename,
                gemini_api_key=api_key,
                clause_store=clause_store,
                timestamp=timestamp,
                pdf_pages=pdf_pages
            )
        
        print(f"✅ Risk analysis complete: Overall score {risk_assessment_dict['overall_score']}")
        
        # Extract clause positions (page-relative)
        print("🔍 Extracting clause positions...")
        extractor = ClauseExtractor(fuzzy_threshold=0.60)
        clause_positions = extractor.extract_clauses_with_positions(
            pdf_pages,
            risk_assessment_dict
        )
        
        print(f"✅ Found {len(clause_positions)} clause positions")
        
        # Transform to absolute positions
        editor_clause_positions = []
        
        for cp in clause_positions:
            # Calculate absolute position
            page_idx = cp.page_number - 1  # Convert to 0-indexed
            
            if page_idx < 0 or page_idx >= len(page_boundaries) - 1:
                print(f"⚠️ Invalid page number {cp.page_number}, skipping clause")
                continue
            
            page_offset = page_boundaries[page_idx]
            absolute_start = page_offset + cp.start_char
            absolute_end = page_offset + cp.end_char
            
            # Generate unique ID for React
            clause_id = str(uuid.uuid4())
            
            editor_clause_positions.append(EditorClausePosition(
                id=clause_id,
                clause_text=cp.clause_text,
                absolute_start=absolute_start,
                absolute_end=absolute_end,
                page_number=cp.page_number,
                risk_score=cp.risk_score,
                risk_severity=cp.risk_severity,
                risk_category=cp.risk_category,
                risk_explanation=cp.risk_explanation,
                recommended_action=cp.recommended_action,
                confidence=cp.confidence
            ))
        
        print(f"✅ Transformed {len(editor_clause_positions)} clauses to absolute positions")
        
        # Prepare metadata
        pdf_metadata = PDFMetadata(
            total_pages=total_pages,
            file_size=file_size,
            filename=file.filename
        )
        
        # Return editor response
        return EditorDocumentResponse(
            full_text=concatenated_text,
            clause_positions=editor_clause_positions,
            page_boundaries=page_boundaries,
            risk_assessment=risk_assessment_dict,
            pdf_metadata=pdf_metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in editor extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF for editor: {str(e)}"
        )


@router.post("/reanalyze-text", response_model=EditorDocumentResponse)
async def reanalyze_text(
    text: str = Form(...),
    gemini_api_key: Optional[str] = Form(None),
    clause_store = Depends(get_clause_store)
):
    """
    Re-analyze edited text from the editor
    
    This endpoint:
    1. Accepts raw text from the editor (after user edits)
    2. Re-runs risk scoring on the modified text
    3. Returns updated clause positions with new absolute positions
    
    Used after user accepts a rewrite to refresh highlighting
    
    Args:
        text: The edited text from the editor
        gemini_api_key: Optional Gemini API key
        
    Returns:
        EditorDocumentResponse with updated analysis and positions
    """
    # Get API key
    api_key = gemini_api_key or GEMINI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key required."
        )
    
    try:
        print("🔄 Re-analyzing edited text...")
        timestamp = datetime.utcnow().isoformat()
        
        # For re-analysis, we treat the entire text as a single "page"
        # since we don't have page boundaries anymore after editing
        pdf_pages = [
            {
                "page_number": 1,
                "text": text
            }
        ]
        
        # Perform risk analysis on edited text
        classification_results, analysis_results, risk_assessment_dict = \
            extract_analyze_and_score_risks(
                full_pdf_text=text,
                source_doc="edited_document.txt",
                gemini_api_key=api_key,
                clause_store=clause_store,
                timestamp=timestamp,
                pdf_pages=pdf_pages
            )
        
        print(f"✅ Re-analysis complete: Overall score {risk_assessment_dict['overall_score']}")
        
        # Extract clause positions
        extractor = ClauseExtractor(fuzzy_threshold=0.60)
        clause_positions = extractor.extract_clauses_with_positions(
            pdf_pages,
            risk_assessment_dict
        )
        
        # Since it's all one "page", absolute positions = page positions
        editor_clause_positions = []
        
        for cp in clause_positions:
            clause_id = str(uuid.uuid4())
            
            editor_clause_positions.append(EditorClausePosition(
                id=clause_id,
                clause_text=cp.clause_text,
                absolute_start=cp.start_char,
                absolute_end=cp.end_char,
                page_number=1,
                risk_score=cp.risk_score,
                risk_severity=cp.risk_severity,
                risk_category=cp.risk_category,
                risk_explanation=cp.risk_explanation,
                recommended_action=cp.recommended_action,
                confidence=cp.confidence
            ))
        
        print(f"✅ Found {len(editor_clause_positions)} clauses in edited text")
        
        # Metadata for edited text
        pdf_metadata = PDFMetadata(
            total_pages=1,
            file_size=len(text.encode('utf-8')),
            filename="edited_document.txt"
        )
        
        return EditorDocumentResponse(
            full_text=text,
            clause_positions=editor_clause_positions,
            page_boundaries=[0, len(text)],
            risk_assessment=risk_assessment_dict,
            pdf_metadata=pdf_metadata
        )
    
    except Exception as e:
        print(f"❌ Error in text re-analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error re-analyzing text: {str(e)}"
        )
