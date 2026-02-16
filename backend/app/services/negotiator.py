"""
Negotiation Agent Service
Provides AI-powered 3-round lease clause negotiation using Groq API.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from groq import Groq


# ================================================================
# Data Classes
# ================================================================

@dataclass
class NegotiationRound:
    """Single round of negotiation"""
    round_number: int  # 0, 1, 2
    counter_clause: str
    justification: str
    risk_reduction: float  # 0-100 (numeric score)
    rejection_text: Optional[str]  # None for round 0
    validation_result: Optional[Dict] = None  # NEW: Optional validation result for counter-clauses


@dataclass
class NegotiationResult:
    """Complete 3-round negotiation result"""
    clause_text: str
    clause_label: str
    risk_score: float
    risk_explanation: str
    stance: str  # "Defensive", "Balanced", "Soft"
    rounds: List[NegotiationRound]  # All 3 rounds
    timestamp: str


# ================================================================
# Negotiation Agent
# ================================================================

class NegotiationAgent:
    """AI-powered lease negotiation agent with 3-round controlled process"""

    ROUND_TYPES = {0: "ideal", 1: "alternative", 2: "fallback"}
    
    REJECTION_TEMPLATES = {
        1: "The counterparty cannot accept this change due to internal policy.",
        2: "The counterparty insists on keeping the original clause."
    }

    # Stance-specific instructions with risk reduction targets
    STANCE_INSTRUCTIONS = {
        "Defensive": {
            "description": "Prioritize tenant safety and fairness. Push for significant changes.",
            "targets": {0: "80-100%", 1: "60-80%", 2: "40-60%"}
        },
        "Balanced": {
            "description": "Seek fair compromises. Propose reasonable modifications.",
            "targets": {0: "60-80%", 1: "40-60%", 2: "30-50%"}
        },
        "Soft": {
            "description": "Maintain good relations. Propose minor modifications.",
            "targets": {0: "40-60%", 1: "30-40%", 2: "20-30%"}
        }
    }

    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        """Initialize Groq client"""
        self.client = Groq(api_key=groq_api_key)
        self.model = model

    def _determine_stance(self, risk_score: float) -> str:
        """
        Determine negotiation stance based on risk score.
        
        Uses explicit if-elif-else logic:
        - risk_score >= 70 → "Defensive"
        - risk_score >= 40 → "Balanced"
        - risk_score < 40 → "Soft"
        """
        if risk_score >= 70:
            return "Defensive"
        elif risk_score >= 40:
            return "Balanced"
        else:
            return "Soft"

    def _build_round_prompt(
        self,
        round_number: int,
        stance: str,
        clause_text: str,
        clause_label: str,
        risk_score: float,
        risk_explanation: str,
        previous_rounds: List[NegotiationRound]
    ) -> str:
        """Build LLM prompt with stance-specific instructions and context"""
        
        stance_info = self.STANCE_INSTRUCTIONS[stance]
        round_type = self.ROUND_TYPES[round_number]
        target_range = stance_info["targets"][round_number]
        
        # Build context based on round number
        if round_number == 0:
            round_context = "This is your FIRST and BEST attempt. Propose your ideal solution."
        elif round_number == 1:
            prev = previous_rounds[0]
            round_context = f"""Your ideal was rejected with this feedback: "{prev.rejection_text}"

Previous proposal (Round 0):
- Counter clause: {prev.counter_clause}
- Risk reduction: {prev.risk_reduction}%

Now propose an ALTERNATIVE approach that's less aggressive but still meaningful."""
        else:  # round_number == 2
            prev0 = previous_rounds[0]
            prev1 = previous_rounds[1]
            round_context = f"""Both proposals were rejected.

Round 0 (Ideal):
- Counter clause: {prev0.counter_clause}
- Risk reduction: {prev0.risk_reduction}%
- Rejection: "{prev0.rejection_text}"

Round 1 (Alternative):
- Counter clause: {prev1.counter_clause}
- Risk reduction: {prev1.risk_reduction}%
- Rejection: "{prev1.rejection_text}"

This is your FINAL attempt. Make minimal but important changes."""

        prompt = f"""You are an expert lease negotiation attorney specializing in tenant representation.

NEGOTIATION STANCE: {stance}
Strategy: {stance_info["description"]}
Target Risk Reduction: {target_range}

ORIGINAL RISKY CLAUSE:
Type: {clause_label}
Risk Score: {risk_score}/100
Risk Explanation: {risk_explanation}
Clause Text: "{clause_text}"

ROUND {round_number} ({round_type.upper()}):
{round_context}

YOUR TASK:
Propose a revised clause that protects the tenant's interests while being appropriate for this {round_type} round.

RESPONSE FORMAT (JSON ONLY - NO MARKDOWN):
{{
  "counter_clause": "Complete revised clause text (max 2000 chars)",
  "justification": "Brief explanation of why this protects tenant (max 200 chars)",
  "risk_reduction": 75.0
}}

CRITICAL RULES:
- risk_reduction must be a NUMBER between 0-100 (NOT a string like "High/Medium/Low")
- Target range for this round: {target_range}
- Return ONLY valid JSON, no markdown code blocks
- Be specific and professional
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate JSON response with simple fallback.
        
        - Try direct JSON parsing first
        - ONE fallback: Extract JSON between first '{' and last '}'
        - Validate required fields and types
        - Truncate if needed
        """
        # Try direct parsing
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: extract JSON from potential markdown wrappers
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON object found in LLM response")
            
            json_str = response_text[start_idx:end_idx + 1]
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON from LLM response: {e}")

        # Validate required fields
        required_fields = ["counter_clause", "justification", "risk_reduction"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate types and ranges
        if not isinstance(data["counter_clause"], str):
            raise ValueError("counter_clause must be a string")
        if not isinstance(data["justification"], str):
            raise ValueError("justification must be a string")
        
        # Handle risk_reduction - convert to float if needed
        try:
            risk_reduction = float(data["risk_reduction"])
            if not (0 <= risk_reduction <= 100):
                raise ValueError("risk_reduction must be between 0-100")
            data["risk_reduction"] = risk_reduction
        except (ValueError, TypeError):
            raise ValueError("risk_reduction must be a number between 0-100")

        # Truncate if needed
        if len(data["counter_clause"]) > 2000:
            data["counter_clause"] = data["counter_clause"][:2000]
        if len(data["justification"]) > 200:
            data["justification"] = data["justification"][:200]

        return data

    def _call_groq_with_retry(self, prompt: str, max_retries: int = 1) -> Dict:
        """
        Call Groq API with simple retry logic.
        
        - Attempt 1: temperature=0.3
        - Attempt 2 (on failure): temperature=0.1 (more deterministic)
        - Use response_format={"type": "json_object"} to force JSON mode
        """
        temperatures = [0.3, 0.1]
        last_error = None

        for attempt, temperature in enumerate(temperatures[:max_retries + 1]):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise legal negotiation expert. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )

                response_text = response.choices[0].message.content
                return self._parse_llm_response(response_text)

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    continue  # Retry with lower temperature
                
        # Both attempts failed
        raise Exception(f"Groq API call failed after {max_retries + 1} attempts: {last_error}")

    def _execute_round(
        self,
        round_number: int,
        stance: str,
        clause_text: str,
        clause_label: str,
        risk_score: float,
        risk_explanation: str,
        previous_rounds: List[NegotiationRound]
    ) -> NegotiationRound:
        """Execute single negotiation round"""
        
        # Build prompt with context
        prompt = self._build_round_prompt(
            round_number=round_number,
            stance=stance,
            clause_text=clause_text,
            clause_label=clause_label,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            previous_rounds=previous_rounds
        )

        # Call Groq with retry
        result = self._call_groq_with_retry(prompt)

        # Add rejection text for rounds 1-2
        rejection_text = None
        if round_number > 0:
            # Add rejection to PREVIOUS round (not current)
            previous_rounds[round_number - 1].rejection_text = self.REJECTION_TEMPLATES[round_number]

        # Create round result
        return NegotiationRound(
            round_number=round_number,
            counter_clause=result["counter_clause"],
            justification=result["justification"],
            risk_reduction=result["risk_reduction"],
            rejection_text=rejection_text  # None for all rounds initially
        )

    def negotiate_clause(
        self,
        clause_text: str,
        clause_label: str,
        risk_score: float,
        risk_explanation: str,
        timestamp: str
    ) -> NegotiationResult:
        """
        Main entry point: Execute 3-round negotiation.
        
        1. Determine stance from risk_score
        2. Execute Round 0 (ideal)
        3. Execute Round 1 (alternative) with round0 context
        4. Execute Round 2 (fallback) with round0 + round1 context
        5. Return NegotiationResult with all 3 rounds
        """
        
        # Determine stance
        stance = self._determine_stance(risk_score)

        # Execute all 3 rounds
        rounds = []
        
        # Round 0: Ideal
        round0 = self._execute_round(
            round_number=0,
            stance=stance,
            clause_text=clause_text,
            clause_label=clause_label,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            previous_rounds=rounds
        )
        rounds.append(round0)

        # Round 1: Alternative
        round1 = self._execute_round(
            round_number=1,
            stance=stance,
            clause_text=clause_text,
            clause_label=clause_label,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            previous_rounds=rounds
        )
        rounds.append(round1)

        # Round 2: Fallback
        round2 = self._execute_round(
            round_number=2,
            stance=stance,
            clause_text=clause_text,
            clause_label=clause_label,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            previous_rounds=rounds
        )
        rounds.append(round2)

        # Return complete result
        return NegotiationResult(
            clause_text=clause_text,
            clause_label=clause_label,
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            stance=stance,
            rounds=rounds,
            timestamp=timestamp
        )

    @staticmethod
    def to_dict(negotiation_result: NegotiationResult) -> Dict[str, Any]:
        """Convert NegotiationResult to dict for JSON serialization"""
        return asdict(negotiation_result)
