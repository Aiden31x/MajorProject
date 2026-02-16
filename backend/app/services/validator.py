"""
Validator Agent for ClauseCraft

This module provides comprehensive clause validation with multi-layered checks:
1. Completeness check (clear parties, obligations, consequences, timeline)
2. Dangerous patterns (unlimited liability, one-sided terms, unclear termination)
3. Contradictions (within clause AND across document)
4. Vague language (ambiguous terms, undefined thresholds)
5. Policy alignment (against company rules, future feature)

IMPORTANT: Validation uses server-side credentials only.
Do NOT accept API keys from frontend for validation.
Reason: Validation is a system responsibility, not user-driven inference.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai


@dataclass
class ValidationIssue:
    """Represents a single validation issue found in a clause"""
    issue_type: str  # "completeness", "contradiction", "dangerous_pattern", "vague_language", "policy_violation"
    severity: str    # "critical", "major", "minor"
    description: str
    location_hint: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationInput:
    """Input data for clause validation"""
    clause_text: str
    clause_category: str
    risk_score: float
    risk_explanation: str
    full_document_context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Result of clause validation"""
    id: str          # UUID for database and frontend reference
    clause_text: str
    status: str      # "PASS", "WARN", "FAIL"
    confidence: float
    issues: List[ValidationIssue]
    timestamp: str
    validation_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "clause_text": self.clause_text,
            "status": self.status,
            "confidence": self.confidence,
            "issues": [issue.to_dict() for issue in self.issues],
            "timestamp": self.timestamp,
            "validation_time_ms": self.validation_time_ms
        }


class ValidationAgent:
    """
    Validator Agent using Gemini 2.5 Flash for comprehensive clause validation.
    
    Uses deterministic temperature (0.2) for consistent results.
    Implements multi-layered validation with clear status determination logic.
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize the ValidationAgent.
        
        Args:
            gemini_api_key: Optional API key. If not provided, uses environment variable.
        """
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")
        
        genai.configure(api_key=api_key)
        # Use stable Gemini 2.5 Flash model (same as RiskScoringAgent for consistency)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
    def _build_validation_prompt(self, validation_input: ValidationInput) -> str:
        """Build the validation prompt for the LLM"""
        
        prompt = f"""You are a legal clause validation expert. Analyze the following contract clause and provide a comprehensive validation assessment.

CLAUSE TO VALIDATE:
{validation_input.clause_text}

CLAUSE CATEGORY: {validation_input.clause_category}
RISK SCORE: {validation_input.risk_score}
RISK EXPLANATION: {validation_input.risk_explanation}

Perform a multi-layered validation:

1. **Completeness Check**: Does the clause have clear:
   - Parties involved
   - Obligations and responsibilities
   - Consequences for non-compliance
   - Timeline or duration
   
2. **Dangerous Patterns**: Look for:
   - Unlimited liability clauses
   - One-sided terms that heavily favor one party
   - Unclear termination conditions
   - Automatic renewal without clear opt-out
   - Indemnification clauses with no caps
   
3. **Contradictions**: Check for:
   - Internal contradictions within the clause
   - Contradictions with other clauses (if document context provided)
   
4. **Vague Language**: Identify:
   - Ambiguous terms without definitions
   - Undefined thresholds or metrics
   - Unclear timeframes ("reasonable time", "promptly", etc.)
   
5. **Policy Alignment**: (Future feature - currently not implemented)

{f"FULL DOCUMENT CONTEXT (for contradiction checking):\n{validation_input.full_document_context[:5000]}\n" if validation_input.full_document_context else ""}

RESPONSE FORMAT:
Provide your analysis as a JSON object with the following structure:
{{
    "confidence": <float between 0 and 1>,
    "issues": [
        {{
            "issue_type": "<completeness|contradiction|dangerous_pattern|vague_language|policy_violation>",
            "severity": "<critical|major|minor>",
            "description": "<detailed description of the issue>",
            "location_hint": "<specific part of clause where issue occurs>"
        }}
    ],
    "overall_assessment": "<brief summary of validation findings>"
}}

IMPORTANT:
- confidence should reflect how certain you are about your assessment (0.0 to 1.0)
- severity levels:
  - critical: Makes clause unacceptable, high risk of legal issues
  - major: Significant concern, needs attention before acceptance
  - minor: Minor improvement suggested, acceptable as-is
- Be precise and specific in your descriptions
- If no issues found, return empty issues array with high confidence
"""
        return prompt
    
    def _determine_status(self, confidence: float, issues: List[ValidationIssue]) -> str:
        """
        Determine validation status based on confidence and issues.
        
        Status determination logic with clear edge case handling:
        
        FAIL: Any critical issue with high confidence (≥0.6) OR overall confidence < 0.6
        Reason: Either we're confident something is broken, or we're too uncertain to recommend
        
        WARN: No critical issues, but one or more major issues
        Reason: Acceptable with caution, user should be aware of concerns
        
        PASS: No critical or major issues and high confidence (≥0.8)
        Reason: Safe to proceed, only minor issues at most
        
        This avoids:
        - FAIL verdicts based on weak evidence
        - WARN when something is clearly broken
        - PASS when confidence is low even without issues
        """
        
        has_critical_issues = any(issue.severity == "critical" for issue in issues)
        has_major_issues = any(issue.severity == "major" for issue in issues)
        
        # FAIL: Any critical issue with high confidence (≥0.6) OR overall confidence < 0.6
        # Reason: Either we're confident something is broken, or we're too uncertain to recommend
        if confidence < 0.6 or (confidence >= 0.6 and has_critical_issues):
            return "FAIL"
        
        # WARN: No critical issues, but one or more major issues
        # Reason: Acceptable with caution, user should be aware of concerns
        elif has_major_issues and not has_critical_issues:
            return "WARN"
        
        # PASS: No critical or major issues and high confidence (≥0.8)
        # Reason: Safe to proceed, only minor issues at most
        else:
            return "PASS"
    
    def validate_clause(self, validation_input: ValidationInput) -> ValidationResult:
        """
        Validate a single clause.
        
        Args:
            validation_input: Input data for validation
            
        Returns:
            ValidationResult with status, confidence, and issues
        """
        start_time = time.time()
        
        try:
            prompt = self._build_validation_prompt(validation_input)
            
            # Use low temperature for deterministic results
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            response_data = json.loads(response_text)
            
            # Extract confidence and issues
            confidence = float(response_data.get("confidence", 0.5))
            issues_data = response_data.get("issues", [])
            
            # Create ValidationIssue objects
            issues = [
                ValidationIssue(
                    issue_type=issue.get("issue_type", "unknown"),
                    severity=issue.get("severity", "minor"),
                    description=issue.get("description", ""),
                    location_hint=issue.get("location_hint", "")
                )
                for issue in issues_data
            ]
            
            # Determine status
            status = self._determine_status(confidence, issues)
            
            # Calculate validation time
            validation_time_ms = (time.time() - start_time) * 1000
            
            return ValidationResult(
                id=str(uuid.uuid4()),  # Generate UUID for frontend/database reference
                clause_text=validation_input.clause_text,
                status=status,
                confidence=confidence,
                issues=issues,
                timestamp=datetime.utcnow().isoformat(),
                validation_time_ms=validation_time_ms
            )
            
        except json.JSONDecodeError as e:
            # Fallback if LLM doesn't return valid JSON
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            
            return ValidationResult(
                id=str(uuid.uuid4()),  # Generate UUID even for errors
                clause_text=validation_input.clause_text,
                status="FAIL",
                confidence=0.0,
                issues=[ValidationIssue(
                    issue_type="system_error",
                    severity="critical",
                    description=f"Validation system error: Unable to parse LLM response",
                    location_hint="N/A"
                )],
                timestamp=datetime.utcnow().isoformat(),
                validation_time_ms=(time.time() - start_time) * 1000
            )
        
        except Exception as e:
            # Catch-all for other errors
            print(f"Validation error: {e}")
            
            return ValidationResult(
                id=str(uuid.uuid4()),  # Generate UUID even for errors
                clause_text=validation_input.clause_text,
                status="FAIL",
                confidence=0.0,
                issues=[ValidationIssue(
                    issue_type="system_error",
                    severity="critical",
                    description=f"Validation system error: {str(e)}",
                    location_hint="N/A"
                )],
                timestamp=datetime.utcnow().isoformat(),
                validation_time_ms=(time.time() - start_time) * 1000
            )
    
    def validate_clauses_batch(
        self,
        clauses: List[ValidationInput],
        max_workers: int = 1  # Changed from 5 to 1 for free tier rate limiting
    ) -> List[ValidationResult]:
        """
        Validate multiple clauses sequentially with rate limiting.

        IMPORTANT: Respects Gemini API free tier limits (5 requests/minute).
        Adds 12-second delay between requests to avoid quota errors.

        Args:
            clauses: List of ValidationInput objects
            max_workers: Maximum number of parallel validation threads (default: 1 for rate limiting)

        Returns:
            List of ValidationResult objects
        """
        results = []

        # Free tier: 5 requests per minute = 1 request every 12 seconds
        RATE_LIMIT_DELAY = 12.0

        print(f"🔄 Validating {len(clauses)} clauses sequentially (12s delay between requests for rate limiting)")

        for i, clause in enumerate(clauses, 1):
            try:
                print(f"   Validating clause {i}/{len(clauses)}...")
                result = self.validate_clause(clause)
                results.append(result)

                # Add delay between requests (except after the last one)
                if i < len(clauses):
                    print(f"   ⏳ Waiting {RATE_LIMIT_DELAY}s before next validation...")
                    time.sleep(RATE_LIMIT_DELAY)

            except Exception as e:
                print(f"❌ Error validating clause {i}: {e}")
                # Add error result
                results.append(ValidationResult(
                    id=str(uuid.uuid4()),
                    clause_text=clause.clause_text,
                    status="FAIL",
                    confidence=0.0,
                    issues=[ValidationIssue(
                        issue_type="system_error",
                        severity="critical",
                        description=f"Batch validation error: {str(e)}",
                        location_hint="N/A"
                    )],
                    timestamp=datetime.utcnow().isoformat(),
                    validation_time_ms=0.0
                ))

        return results


# Utility function for database storage
async def store_validation_result(
    validation_result: ValidationResult,
    document_source: str,
    prisma_client
) -> str:
    """
    Store validation result in PostgreSQL.
    
    Args:
        validation_result: ValidationResult object
        document_source: Source document identifier
        prisma_client: Prisma client instance
        
    Returns:
        ID of the created validation result record
    """
    record = await prisma_client.validationresult.create(
        data={
            "clauseText": validation_result.clause_text,
            "clauseCategory": "",  # Will be populated from validation_input
            "riskScore": 0.0,  # Will be populated from validation_input
            "status": validation_result.status,
            "confidence": validation_result.confidence,
            "issues": [issue.to_dict() for issue in validation_result.issues],
            "documentSource": document_source,
            "timestamp": datetime.fromisoformat(validation_result.timestamp),
            "validationTimeMs": validation_result.validation_time_ms
        }
    )
    
    return record.id
