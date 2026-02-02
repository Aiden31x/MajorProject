"""
Risk Scoring Agent for ClauseCraft
Provides multi-dimensional risk assessment for lease agreements
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
import google.generativeai as genai
from app.config import GEMINI_MODEL


@dataclass
class ClauseRiskScore:
    """Individual clause risk assessment"""
    clause_text: str
    category: str  # financial, legal, operational, timeline, strategic
    severity: float  # 0-100
    severity_level: str  # Low, Medium, High
    confidence: float  # 0-1
    risk_explanation: str
    recommended_action: str


@dataclass
class DimensionScore:
    """Risk score for one dimension"""
    score: float  # 0-100
    severity: str  # Low, Medium, High
    weight: Optional[float]  # Percentage weight in overall score (None for qualitative)
    key_findings: List[str]
    problematic_clauses: List[ClauseRiskScore]


@dataclass
class RiskAssessment:
    """Complete risk assessment for a lease agreement"""
    overall_score: float  # 0-100 (weighted average of 4 quantitative dimensions)
    overall_severity: str  # Low, Medium, High
    financial: DimensionScore
    legal_compliance: DimensionScore
    operational: DimensionScore
    timeline: DimensionScore
    strategic_reputational: DimensionScore  # Qualitative only
    top_risks: List[str]
    immediate_actions: List[str]
    negotiation_priorities: List[str]
    total_clauses_analyzed: int
    high_risk_clauses_count: int
    timestamp: str


class RiskScoringAgent:
    """
    Multi-dimensional risk scoring agent using Gemini LLM.
    
    Features:
    - 5 dimensional risk analysis (4 quantitative + 1 qualitative)
    - Single optimized LLM call for efficiency
    - Weighted aggregation for overall score
    - Retry mechanism for robust JSON parsing
    - Structured scoring rubrics for consistency
    """
    
    # Dimension weights (must sum to 1.0)
    WEIGHTS = {
        "financial": 0.35,
        "legal_compliance": 0.30,
        "operational": 0.20,
        "timeline": 0.15,
        "strategic_reputational": None  # Qualitative only, not in overall score
    }
    
    def __init__(self, gemini_api_key: str):
        """Initialize the risk scoring agent"""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def _get_severity_level(self, score: float) -> str:
        """Map numerical score to severity level (non-overlapping thresholds)"""
        if score <= 39:
            return "Low"
        elif score <= 69:
            return "Medium"
        else:
            return "High"
    
    def _build_scoring_prompt(self, full_pdf_text: str, historical_context: str, pdf_pages: List[Dict] = None) -> str:
        """Construct the comprehensive risk scoring prompt"""

        # Calculate page boundaries for position extraction
        page_info = ""
        if pdf_pages:
            page_info = "\n**PAGE BOUNDARIES (for position extraction):**\n"
            current_pos = 0
            for page in pdf_pages[:min(10, len(pdf_pages))]:  # Show first 10 pages as examples
                page_text = page.get('text', '')
                end_pos = current_pos + len(page_text)
                page_info += f"Page {page.get('page_number', 0)}: chars {current_pos}-{end_pos}\n"
                current_pos = end_pos
            page_info += "\n"

        prompt = f"""You are a legal risk assessment expert analyzing a lease agreement. Provide a comprehensive multi-dimensional risk analysis.

**LEASE AGREEMENT TEXT:**
{full_pdf_text}

{historical_context}
{page_info}

**YOUR TASK:**
Analyze this lease agreement across 5 risk dimensions and provide a structured JSON response.

**SCORING RUBRICS (0-100 scale):**

**1. FINANCIAL RISK (Weight: 35%)**
- 0-30 (Low): Reasonable rent, clear payment terms, normal escalation (<3% annual), standard deposit
- 31-60 (Medium): Moderate rent escalation (3-5%), multiple hidden costs, unclear VAT terms, high deposit
- 61-100 (High): Excessive rent escalation (>5%), unfair payment terms, unreasonable deposits, hidden fees, one-sided financial clauses

Key factors: Payment terms, rent escalation clauses, deposits, hidden costs, VAT terms, financial penalties

**2. LEGAL/COMPLIANCE RISK (Weight: 30%)**
- 0-30 (Low): Balanced liability, standard insurance, fair indemnification, tenant protections, clear compliance terms
- 31-60 (Medium): Moderate liability imbalance, some missing protections, unclear compliance requirements
- 61-100 (High): One-sided liability allocation, unlimited indemnification, missing tenant protections, unfair legal clauses, compliance gaps

Key factors: Liability allocation, indemnification clauses, insurance requirements, tenant protections, regulatory compliance

**3. OPERATIONAL RISK (Weight: 20%)**
- 0-30 (Low): Flexible use rights, reasonable maintenance terms, fair access requirements, permitted sublease/assignment
- 31-60 (Medium): Some use restrictions, moderate maintenance burden, limited sublease rights
- 61-100 (High): Severe use restrictions, excessive maintenance obligations, landlord overreach, prohibited sublease/assignment, operational constraints

Key factors: Use restrictions, maintenance obligations, access rights, sublease/assignment terms, operational flexibility

**4. TIMELINE RISK (Weight: 15%)**
- 0-30 (Low): Reasonable notice periods (<6 months), no auto-renewal, clear break clauses, flexible termination
- 31-60 (Medium): Long notice periods (6-12 months), short-term auto-renewal (<1 year), limited break clauses
- 61-100 (High): Excessive notice periods (>12 months), long auto-renewal (>1 year), no break clauses, inflexible timeline

Key factors: Notice periods, auto-renewal terms, break clauses, lease flexibility, termination conditions

**5. STRATEGIC/REPUTATIONAL RISK (Qualitative only - insights, not scored in overall)**
- Brand/trademark usage restrictions
- Confidentiality imbalances
- Non-disparagement clauses
- Publicity restrictions
- Reputational implications

**OUTPUT FORMAT:**
Return a JSON object with this EXACT structure (no markdown, no explanation, just the JSON):

{{
  "financial": {{
    "score": <0-100>,
    "key_findings": ["finding 1", "finding 2", "finding 3"],
    "problematic_clauses": [
      {{
        "clause_text": "Brief clause reference (max 100 chars)",
        "page_number": <integer page number>,
        "start_char": <integer char position in full text>,
        "end_char": <integer char position in full text>,
        "severity": <0-100>,
        "confidence": <0-1>,
        "risk_explanation": "Brief explanation (max 150 chars)",
        "recommended_action": "Brief action (max 100 chars)"
      }}
    ]
  }},
  "legal_compliance": {{
    "score": <0-100>,
    "key_findings": ["finding 1", "finding 2"],
    "problematic_clauses": [...]
  }},
  "operational": {{
    "score": <0-100>,
    "key_findings": ["finding 1", "finding 2"],
    "problematic_clauses": [...]
  }},
  "timeline": {{
    "score": <0-100>,
    "key_findings": ["finding 1", "finding 2"],
    "problematic_clauses": [...]
  }},
  "strategic_reputational": {{
    "score": 0,
    "key_findings": ["insight 1", "insight 2"],
    "problematic_clauses": []
  }},
  "top_risks": ["risk 1", "risk 2", "risk 3"],
  "immediate_actions": ["action 1", "action 2"],
  "total_clauses_analyzed": <count>
}}

**CRITICAL OUTPUT SIZE REQUIREMENTS:**
- clause_text: MUST be under 100 chars - use section references like "Section 1.01.17 Operating Expenses" NOT the full text
- risk_explanation: MUST be under 150 chars
- recommended_action: MUST be under 100 chars
- key_findings: Max 3 findings per dimension, each under 150 chars
- problematic_clauses: Max 3 per dimension (not 5)
- All scores: numbers 0-100
- All confidence values: 0-1
- Strategic score is always 0 (qualitative-only dimension)
- Be concise - the response MUST be valid JSON under 10000 characters total

**POSITION EXTRACTION REQUIREMENTS:**
For EVERY problematic clause, you MUST include page_number in the JSON. This is MANDATORY.

Set start_char and end_char to -1 (we will search for exact positions later), but page_number is REQUIRED.

If you're unsure of the page number, estimate based on where in the document the clause appears:
- Early in document → page_number between 1-8
- Middle of document → page_number between 9-16
- Late in document → page_number between 17-24

DO NOT leave page_number as -1. Every clause must have a page number estimate."""
        
        return prompt
    
    def _truncate_string(self, s: str, max_len: int) -> str:
        """Truncate string to max length with ellipsis"""
        if len(s) <= max_len:
            return s
        return s[:max_len - 3] + "..."

    def _sanitize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize response by truncating overly long strings"""
        for dim in ["financial", "legal_compliance", "operational", "timeline", "strategic_reputational"]:
            if dim in data:
                # Truncate key findings
                if "key_findings" in data[dim]:
                    data[dim]["key_findings"] = [
                        self._truncate_string(f, 150) for f in data[dim]["key_findings"][:3]
                    ]
                # Truncate and limit problematic clauses
                if "problematic_clauses" in data[dim]:
                    clauses = data[dim]["problematic_clauses"][:3]  # Max 3
                    for clause in clauses:
                        if "clause_text" in clause:
                            clause["clause_text"] = self._truncate_string(clause["clause_text"], 100)
                        if "risk_explanation" in clause:
                            clause["risk_explanation"] = self._truncate_string(clause["risk_explanation"], 150)
                        if "recommended_action" in clause:
                            clause["recommended_action"] = self._truncate_string(clause["recommended_action"], 100)
                    data[dim]["problematic_clauses"] = clauses

        # Truncate top-level lists
        for field in ["top_risks", "immediate_actions"]:
            if field in data:
                data[field] = [self._truncate_string(item, 150) for item in data[field][:3]]

        return data

    def _attempt_json_repair(self, response_text: str) -> str:
        """Attempt to repair truncated JSON by closing open structures"""
        # Count open brackets
        open_braces = response_text.count('{') - response_text.count('}')
        open_brackets = response_text.count('[') - response_text.count(']')

        # Check if we're in the middle of a string
        in_string = False
        escaped = False
        for char in response_text:
            if escaped:
                escaped = False
                continue
            if char == '\\':
                escaped = True
                continue
            if char == '"':
                in_string = not in_string

        repaired = response_text

        # Close string if needed
        if in_string:
            repaired += '"'

        # Close brackets and braces
        repaired += ']' * open_brackets
        repaired += '}' * open_braces

        return repaired

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate LLM JSON response"""
        response_text = response_text.strip()

        # Since we're using response_mime_type="application/json", try direct parsing first
        data = None
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ Initial parse failed: {e}")
            # Try to repair truncated JSON
            try:
                repaired = self._attempt_json_repair(response_text)
                data = json.loads(repaired)
                print("✅ JSON repair successful")
            except json.JSONDecodeError:
                # Fallback: Extract JSON block if LLM added extra text
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')

                if start_idx == -1 or end_idx == -1:
                    raise ValueError("No JSON object found in response")

                json_str = response_text[start_idx:end_idx + 1]
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    # Last attempt: repair the extracted JSON
                    repaired = self._attempt_json_repair(json_str)
                    data = json.loads(repaired)
                    print("✅ JSON repair successful on extracted block")

        # Validate and fill in missing fields with defaults
        required_dimensions = ["financial", "legal_compliance", "operational", "timeline", "strategic_reputational"]
        default_dim = {
            "score": 50,
            "key_findings": ["Analysis incomplete for this dimension"],
            "problematic_clauses": []
        }

        for dim in required_dimensions:
            if dim not in data:
                print(f"⚠️ Missing dimension {dim}, using default")
                data[dim] = default_dim.copy()
            else:
                if "score" not in data[dim]:
                    data[dim]["score"] = 50
                if "key_findings" not in data[dim]:
                    data[dim]["key_findings"] = ["Analysis incomplete"]
                if "problematic_clauses" not in data[dim]:
                    data[dim]["problematic_clauses"] = []

                # Validate optional position fields in problematic_clauses
                for clause in data[dim].get("problematic_clauses", []):
                    clause['page_number'] = clause.get('page_number', -1)
                    clause['start_char'] = clause.get('start_char', -1)
                    clause['end_char'] = clause.get('end_char', -1)

                    # Ensure valid ranges
                    if not isinstance(clause['page_number'], int) or clause['page_number'] < -1:
                        clause['page_number'] = -1
                    if not isinstance(clause['start_char'], int) or clause['start_char'] < -1:
                        clause['start_char'] = -1
                    if not isinstance(clause['end_char'], int) or clause['end_char'] < -1:
                        clause['end_char'] = -1

        # Fill in missing aggregation fields
        if "top_risks" not in data:
            data["top_risks"] = ["Risk analysis incomplete"]
        if "immediate_actions" not in data:
            data["immediate_actions"] = ["Review analysis manually"]
        if "negotiation_priorities" not in data:
            data["negotiation_priorities"] = []  # Empty - use negotiation agent instead
        if "total_clauses_analyzed" not in data:
            data["total_clauses_analyzed"] = 0

        # Sanitize to ensure string lengths are within bounds
        data = self._sanitize_response(data)

        return data
    
    def _create_safe_default_response(self) -> Dict[str, Any]:
        """Create a safe default response when parsing fails"""
        return {
            "financial": {
                "score": 50,
                "key_findings": ["Analysis incomplete - JSON parsing failed"],
                "problematic_clauses": []
            },
            "legal_compliance": {
                "score": 50,
                "key_findings": ["Analysis incomplete - JSON parsing failed"],
                "problematic_clauses": []
            },
            "operational": {
                "score": 50,
                "key_findings": ["Analysis incomplete - JSON parsing failed"],
                "problematic_clauses": []
            },
            "timeline": {
                "score": 50,
                "key_findings": ["Analysis incomplete - JSON parsing failed"],
                "problematic_clauses": []
            },
            "strategic_reputational": {
                "score": 0,
                "key_findings": ["Analysis incomplete - JSON parsing failed"],
                "problematic_clauses": []
            },
            "top_risks": ["Unable to assess - analysis incomplete"],
            "immediate_actions": ["Retry analysis or review manually"],
            "negotiation_priorities": [],  # Empty - use negotiation agent instead
            "total_clauses_analyzed": 0
        }
    
    def _call_llm_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Call LLM with retry mechanism for robust JSON parsing"""
        
        # First attempt: Temperature 0.3 for balanced consistency and nuance
        try:
            print("🤖 Step 3/3: Generating risk assessment (attempt 1 - temp 0.3)...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=16384,
                    response_mime_type="application/json"
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from LLM")
            
            data = self._parse_llm_response(response.text)
            print("✅ Risk assessment parsed successfully (attempt 1)")
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ JSON parsing failed on attempt 1: {e}")
            print(f"📄 Raw response (first 1000 chars): {response.text[:1000]}")
            print("🔄 Retrying with temperature 0.1 for more deterministic output...")
        
        # Second attempt: Temperature 0.1 for more deterministic output
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=16384,
                    response_mime_type="application/json"
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from LLM")
            
            data = self._parse_llm_response(response.text)
            print("✅ Risk assessment parsed successfully (attempt 2)")
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ JSON parsing failed on attempt 2: {e}")
            print(f"📄 Raw response (first 1000 chars): {response.text[:1000]}")
            print("⚠️ Falling back to safe default response")
            return self._create_safe_default_response()
    
    def score_lease_agreement(
        self,
        full_pdf_text: str,
        historical_context: str = "",
        timestamp: str = "",
        pdf_pages: List[Dict] = None
    ) -> RiskAssessment:
        """
        Score a lease agreement across 5 dimensions.

        Args:
            full_pdf_text: Complete text from the PDF
            historical_context: Optional historical context from RAG
            timestamp: ISO timestamp for the assessment
            pdf_pages: Optional list of page dicts with 'page_number' and 'text' for position extraction

        Returns:
            RiskAssessment object with complete analysis
        """
        # Build prompt
        prompt = self._build_scoring_prompt(full_pdf_text, historical_context, pdf_pages)
        
        # Call LLM with retry mechanism
        data = self._call_llm_with_retry(prompt)
        
        # Calculate overall score (weighted average of 4 quantitative dimensions)
        overall_score = (
            data["financial"]["score"] * self.WEIGHTS["financial"] +
            data["legal_compliance"]["score"] * self.WEIGHTS["legal_compliance"] +
            data["operational"]["score"] * self.WEIGHTS["operational"] +
            data["timeline"]["score"] * self.WEIGHTS["timeline"]
        )
        
        overall_severity = self._get_severity_level(overall_score)
        
        # Convert to dataclasses
        def parse_clause(clause_dict: Dict) -> ClauseRiskScore:
            return ClauseRiskScore(
                clause_text=clause_dict.get("clause_text", ""),
                category=clause_dict.get("category", "unknown"),
                severity=float(clause_dict.get("severity", 0)),
                severity_level=self._get_severity_level(float(clause_dict.get("severity", 0))),
                confidence=float(clause_dict.get("confidence", 0.5)),
                risk_explanation=clause_dict.get("risk_explanation", ""),
                recommended_action=clause_dict.get("recommended_action", "")
            )
        
        def parse_dimension(dim_name: str, dim_data: Dict, weight: Optional[float]) -> DimensionScore:
            clauses = [parse_clause({**c, "category": dim_name}) for c in dim_data.get("problematic_clauses", [])]
            return DimensionScore(
                score=float(dim_data.get("score", 0)),
                severity=self._get_severity_level(float(dim_data.get("score", 0))),
                weight=weight,
                key_findings=dim_data.get("key_findings", []),
                problematic_clauses=clauses
            )
        
        # Count high-risk clauses
        all_clauses = []
        for dim in ["financial", "legal_compliance", "operational", "timeline", "strategic_reputational"]:
            all_clauses.extend(data[dim].get("problematic_clauses", []))
        
        high_risk_count = sum(1 for c in all_clauses if float(c.get("severity", 0)) >= 70)
        
        # Build RiskAssessment
        risk_assessment = RiskAssessment(
            overall_score=round(overall_score, 1),
            overall_severity=overall_severity,
            financial=parse_dimension("financial", data["financial"], self.WEIGHTS["financial"]),
            legal_compliance=parse_dimension("legal_compliance", data["legal_compliance"], self.WEIGHTS["legal_compliance"]),
            operational=parse_dimension("operational", data["operational"], self.WEIGHTS["operational"]),
            timeline=parse_dimension("timeline", data["timeline"], self.WEIGHTS["timeline"]),
            strategic_reputational=parse_dimension("strategic_reputational", data["strategic_reputational"], None),
            top_risks=data.get("top_risks", []),
            immediate_actions=data.get("immediate_actions", []),
            negotiation_priorities=data.get("negotiation_priorities", []),
            total_clauses_analyzed=data.get("total_clauses_analyzed", len(all_clauses)),
            high_risk_clauses_count=high_risk_count,
            timestamp=timestamp
        )
        
        print(f"✅ Risk assessment complete: Overall score {overall_score:.1f} ({overall_severity})")
        print(f"📊 Dimensional scores: Financial={data['financial']['score']}, Legal={data['legal_compliance']['score']}, Operational={data['operational']['score']}, Timeline={data['timeline']['score']}")
        
        return risk_assessment
    
    @staticmethod
    def to_dict(risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Convert RiskAssessment to dictionary for JSON serialization"""
        return asdict(risk_assessment)
