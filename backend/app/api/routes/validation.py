"""
Validation API Routes for ClauseCraft

IMPORTANT: Validation uses server-side Gemini API credentials only.
Do NOT accept API keys from frontend for validation.

Reason: Validation is a system responsibility, not user-driven inference.
This ensures consistent validation logic and security.
"""

from fastapi import APIRouter, Form, HTTPException, Query
from typing import Optional, List
import os
from datetime import datetime

from app.services.validator import ValidationAgent, ValidationInput
from app.models.responses import (
    ValidationResponse,
    ValidationIssueResponse,
    BatchValidationResponse
)

router = APIRouter()

# Get server-side Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


@router.post("/validate-clause", response_model=ValidationResponse)
async def validate_clause(
    clause_text: str = Form(...),
    clause_category: str = Form(...),
    risk_score: float = Form(...),
    risk_explanation: str = Form(...),
    full_document_text: Optional[str] = Form(None)
):
    """
    Validate a single clause on-demand.

    IMPORTANT: Validation uses server-side Gemini API credentials only.
    Do NOT accept API keys from frontend for validation.

    Reason: Validation is a system responsibility, not user-driven inference.
    This ensures consistent validation logic and security.

    Args:
        clause_text: The text of the clause to validate
        clause_category: Category/type of the clause
        risk_score: Risk score of the clause (0-100)
        risk_explanation: Explanation of why the clause is risky
        full_document_text: Optional full document context for contradiction checking

    Returns:
        ValidationResponse with status, confidence, and issues
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Validation service not configured: GEMINI_API_KEY not set"
        )

    try:
        # Initialize validator with server-side credentials
        validator = ValidationAgent(GEMINI_API_KEY)

        # Create validation input
        validation_input = ValidationInput(
            clause_text=clause_text,
            clause_category=clause_category,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            full_document_context=full_document_text[:50000] if full_document_text else None
        )

        # Perform validation
        result = validator.validate_clause(validation_input)

        # Convert to API response format
        return ValidationResponse(
            clause_text=result.clause_text,
            status=result.status,
            confidence=result.confidence,
            issues=[
                ValidationIssueResponse(
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    description=issue.description,
                    location_hint=issue.location_hint
                )
                for issue in result.issues
            ],
            timestamp=result.timestamp,
            validation_time_ms=result.validation_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/validate-batch", response_model=BatchValidationResponse)
async def validate_batch_clauses(
    clauses: List[dict],  # List of clause dictionaries with required fields
    max_workers: int = Form(5)
):
    """
    Validate multiple clauses in parallel.

    Args:
        clauses: List of clause dictionaries, each containing:
            - clause_text: str
            - clause_category: str
            - risk_score: float
            - risk_explanation: str
            - full_document_text: Optional[str]
        max_workers: Maximum number of parallel validation threads

    Returns:
        BatchValidationResponse with all validation results
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Validation service not configured: GEMINI_API_KEY not set"
        )

    try:
        # Initialize validator
        validator = ValidationAgent(GEMINI_API_KEY)

        # Create validation inputs
        validation_inputs = []
        for clause_dict in clauses:
            validation_inputs.append(ValidationInput(
                clause_text=clause_dict.get("clause_text", ""),
                clause_category=clause_dict.get("clause_category", ""),
                risk_score=clause_dict.get("risk_score", 0.0),
                risk_explanation=clause_dict.get("risk_explanation", ""),
                full_document_context=clause_dict.get("full_document_text", "")[:50000] if clause_dict.get("full_document_text") else None
            ))

        # Perform batch validation
        start_time = datetime.now()
        results = validator.validate_clauses_batch(validation_inputs, max_workers=max_workers)
        total_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Count results by status
        passed_count = sum(1 for r in results if r.status == "PASS")
        warned_count = sum(1 for r in results if r.status == "WARN")
        failed_count = sum(1 for r in results if r.status == "FAIL")

        # Convert to API response format
        return BatchValidationResponse(
            results=[
                ValidationResponse(
                    clause_text=result.clause_text,
                    status=result.status,
                    confidence=result.confidence,
                    issues=[
                        ValidationIssueResponse(
                            issue_type=issue.issue_type,
                            severity=issue.severity,
                            description=issue.description,
                            location_hint=issue.location_hint
                        )
                        for issue in result.issues
                    ],
                    timestamp=result.timestamp,
                    validation_time_ms=result.validation_time_ms
                )
                for result in results
            ],
            total_validated=len(results),
            passed_count=passed_count,
            warned_count=warned_count,
            failed_count=failed_count,
            total_time_ms=total_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch validation error: {str(e)}"
        )


@router.get("/health")
async def validation_health():
    """
    Health check for validation service.

    Returns:
        Status information about the validation service
    """
    return {
        "status": "healthy" if GEMINI_API_KEY else "unavailable",
        "service": "ValidationAgent",
        "model": "gemini-2.0-flash-exp",
        "api_key_configured": bool(GEMINI_API_KEY)
    }
