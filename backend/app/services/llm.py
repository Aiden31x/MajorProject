"""
LLM service for ClauseCraft - Extracted from original app.py
Handles Gemini LLM interactions for PDF analysis and conversational RAG
"""
from typing import List, Tuple, Dict, Any
from collections import defaultdict
import google.generativeai as genai
from app.config import GEMINI_MODEL, LEASE_LABEL_MAP


# System prompt for conversational RAG assistant
CONVERSATIONAL_SYSTEM_PROMPT = """You are a helpful legal assistant specializing in lease agreements. Your role is to answer questions about lease clauses stored in a knowledge base.

Guidelines:
- Base your answers on the retrieved clause evidence provided
- Be conversational and helpful
- If the retrieved clauses don't fully answer the question, acknowledge this
- Cite specific clause types and sources when relevant
- For red flags, explain the risks clearly
- Maintain context from previous conversation turns
- If unsure, say so rather than making up information

Remember: You're helping users understand lease agreements and identify potential issues."""


def extract_and_analyze_with_llm(
    full_pdf_text: str,
    source_doc: str,
    gemini_api_key: str,
    clause_store  # ClauseStore instance
) -> Tuple[str, str]:
    """
    Use LLM (Gemini) to extract and classify clauses from full PDF text, with RAG grounding.

    This approach is more accurate than regex-based splitting because:
    - LLM understands context and clause boundaries
    - Classification happens with full document context
    - Preserves semantic relationships between clauses

    Args:
        full_pdf_text: Complete text from PDF
        source_doc: Source document filename
        gemini_api_key: Google Gemini API key
        clause_store: ClauseStore instance for RAG context

    Returns:
        Tuple of (classification_results_markdown, analysis_markdown)
    """
    # Configure Gemini API
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Retrieve similar documents from RAG for context
    historical_context = ""
    try:
        stats = clause_store.get_statistics()
        if stats['total_clauses'] > 0:
            # Get similar past documents
            similar_docs = clause_store.retrieve_similar_clauses(
                query=full_pdf_text[:1000],  # Use first 1000 chars for similarity
                top_k=3,
                label_filter=None
            )

            if similar_docs:
                historical_context = "\n\n--- HISTORICAL CONTEXT FROM KNOWLEDGE BASE ---\n"
                historical_context += "Similar lease agreements found:\n"
                for i, doc in enumerate(similar_docs, 1):
                    historical_context += f"\n{i}. From {doc['metadata'].get('source_doc', 'Unknown')}:\n"
                    historical_context += f"   {doc['text'][:200]}...\n"
    except Exception as e:
        print(f"⚠️ Could not retrieve historical context: {e}")

    # Truncate PDF text if too long (keep under 4000 tokens ≈ 16000 chars)
    pdf_text_truncated = full_pdf_text[:12000] if len(full_pdf_text) > 12000 else full_pdf_text

    # Build complete category list from ALBERT's 26 categories
    categories_list = "\n   - ".join([f"{label} ({idx})" for idx, label in sorted(LEASE_LABEL_MAP.items())])

    # Prompt 1: Classification with all 26 categories
    classification_prompt = f"""You are a legal expert analyzing a lease agreement. Your task is to extract and classify ALL important clauses using our fine-tuned classification system.

**CLASSIFICATION CATEGORIES (26 total):**
   - {categories_list}

**INSTRUCTIONS:**
1. Extract ALL important clauses from the lease agreement
2. Classify each clause into ONE of the 26 categories above
3. Prioritize identifying "redflag" and "redflags" - these are unfair, risky, or problematic terms
4. For each clause provide:
   - The exact clause text
   - Its category classification
   - Brief explanation (mandatory for red flags)

**LEASE AGREEMENT TEXT:**
{pdf_text_truncated}
{historical_context}

**OUTPUT FORMAT (Markdown):**

## 📋 Classified Clauses

### 🚩 Red Flags & Problematic Clauses
(List all redflag/redflags clauses here with detailed explanations)

**1. redflag**
- **Clause:** [exact text]
- **Risk:** [explain why this is problematic]

### 👥 Parties
**Lessor:**
- [clause text]

**Lessee:**
- [clause text]

### 📅 Dates & Terms
**Start Date:**
- [clause text]

**End Date:**
- [clause text]

**Expiration Date:**
- [clause text]

### 💰 Financial Terms
**Term of Payment:**
- [clause text]

**Rent Review Date:**
- [clause text]

**VAT:**
- [clause text]

**Indexation Rent:**
- [clause text]

### 📍 Property Details
**Leased Space:**
- [clause text]

**Designated Use:**
- [clause text]

### 📄 Other Important Clauses
(Group remaining clauses by their categories: notice_period, extension_period, type_lease, Agreement_Type, clause_number, clause_title, etc.)

Please be thorough and classify EVERY important clause from the document."""

    # Prompt 2: AI Analysis and insights
    analysis_prompt = f"""You are a legal expert providing analysis and recommendations for a lease agreement.

**LEASE AGREEMENT TEXT:**
{pdf_text_truncated}
{historical_context}

**YOUR TASK:**
Provide a comprehensive AI-powered analysis of this lease agreement. Focus on:

1. **Executive Summary**
   - Type of lease agreement
   - Key parties involved
   - Property details
   - Lease duration and dates

2. **Financial Overview**
   - Rent amount and payment terms
   - Deposit/security requirements
   - VAT implications
   - Rent review/indexation clauses
   - Total financial commitment

3. **Risk Assessment**
   - Overall risk level (Low/Medium/High)
   - Key red flags identified
   - Potential legal issues
   - Unfavorable terms for tenant
   - Missing standard protections

4. **Rights & Obligations**
   - Tenant rights
   - Landlord obligations
   - Termination conditions
   - Notice periods

5. **Recommendations**
   - Points to negotiate
   - Clauses to clarify
   - Legal review suggestions
   - Actions to take before signing

**OUTPUT FORMAT:**
Use clear markdown headings and bullet points. Be specific, actionable, and focus on practical insights that help the tenant make informed decisions.

Provide honest, balanced analysis - highlight both favorable and unfavorable terms."""

    try:
        # Step 1: Get classification results
        print("🤖 Step 1/2: Classifying clauses with Gemini...")
        classification_response = model.generate_content(
            classification_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,  # Lower temperature for consistent classification
                max_output_tokens=16384  # Increased significantly for complete classification
            )
        )

        if not classification_response.text:
            if hasattr(classification_response, 'prompt_feedback'):
                return f"⚠️ Classification blocked: {classification_response.prompt_feedback}", ""
            return "⚠️ Empty classification response from Gemini", ""

        classification_results = classification_response.text

        # Check if classification was truncated - improved detection
        if hasattr(classification_response, 'candidates') and len(classification_response.candidates) > 0:
            finish_reason = str(classification_response.candidates[0].finish_reason)
            print(f"📊 Classification finish reason: {finish_reason}")
            print(f"📏 Classification response length: {len(classification_results)} characters")

            # Check for any kind of truncation
            if 'MAX_TOKENS' in finish_reason or 'LENGTH' in finish_reason or finish_reason == 'MAX_TOKENS':
                classification_results += "\n\n⚠️ **Note:** Response was truncated due to length. Consider processing a shorter document or contact support."

        # Step 2: Get AI analysis
        print("🤖 Step 2/2: Generating AI analysis...")
        analysis_response = model.generate_content(
            analysis_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.4,  # Slightly higher for more nuanced analysis
                max_output_tokens=8192  # Increased for complete analysis
            )
        )

        if not analysis_response.text:
            if hasattr(analysis_response, 'prompt_feedback'):
                analysis_results = f"⚠️ Analysis blocked: {analysis_response.prompt_feedback}"
            else:
                analysis_results = "⚠️ Empty analysis response from Gemini"
        else:
            analysis_results = analysis_response.text

            # Check if analysis was truncated - improved detection
            if hasattr(analysis_response, 'candidates') and len(analysis_response.candidates) > 0:
                finish_reason = str(analysis_response.candidates[0].finish_reason)
                print(f"📊 Analysis finish reason: {finish_reason}")
                print(f"📏 Analysis response length: {len(analysis_results)} characters")

                if 'MAX_TOKENS' in finish_reason or 'LENGTH' in finish_reason or finish_reason == 'MAX_TOKENS':
                    analysis_results += "\n\n⚠️ **Note:** Analysis was truncated due to length."

        print("✅ Classification and analysis complete!")
        print(f"📊 Final classification length: {len(classification_results)} chars")
        print(f"📊 Final analysis length: {len(analysis_results)} chars")

        # Safety check - warn if responses seem too short
        if len(classification_results) < 500:
            print("⚠️ WARNING: Classification results seem unusually short!")
        if len(analysis_results) < 500:
            print("⚠️ WARNING: Analysis results seem unusually short!")

        return classification_results, analysis_results

    except Exception as e:
        error_msg = f"⚠️ Error during Gemini processing: {str(e)}"
        print(f"❌ Full error: {e}")
        import traceback
        traceback.print_exc()
        return error_msg, error_msg


def extract_analyze_and_score_risks(
    full_pdf_text: str,
    source_doc: str,
    gemini_api_key: str,
    clause_store,  # ClauseStore instance
    timestamp: str = "",
    pdf_pages: List[Dict] = None  # NEW parameter
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Complete 3-step pipeline: Classification → Analysis → Risk Scoring.

    Args:
        full_pdf_text: Complete text from PDF
        source_doc: Source document filename
        gemini_api_key: Google Gemini API key
        clause_store: ClauseStore instance for RAG context
        timestamp: ISO timestamp for the assessment
        pdf_pages: Optional list of page dicts with 'page_number' and 'text' for position extraction

    Returns:
        Tuple of (classification_results, analysis_results, risk_assessment_dict)
    """
    from app.services.risk_scorer import RiskScoringAgent
    
    print("🚀 Starting 3-step pipeline: Classification → Analysis → Risk Scoring")
    
    # Steps 1-2: Classification and Analysis (existing function)
    classification_results, analysis_results = extract_and_analyze_with_llm(
        full_pdf_text,
        source_doc,
        gemini_api_key,
        clause_store
    )
    
    # Step 3: Risk Scoring
    try:
        # Retrieve historical context from RAG for risk calibration
        historical_context = ""
        try:
            stats = clause_store.get_statistics()
            if stats['total_clauses'] > 0:
                # Get similar past documents
                similar_docs = clause_store.retrieve_similar_clauses(
                    query=full_pdf_text[:1000],
                    top_k=3,
                    label_filter=None
                )
                
                if similar_docs:
                    historical_context = "\n\n--- HISTORICAL RISK CONTEXT FROM KNOWLEDGE BASE ---\n"
                    historical_context += "Similar lease agreements found for risk calibration:\n"
                    for i, doc in enumerate(similar_docs, 1):
                        metadata = doc['metadata']
                        # Check if this document has risk scores
                        if metadata.get('overall_risk_score'):
                            historical_context += f"\n{i}. From {metadata.get('source_doc', 'Unknown')}:\n"
                            historical_context += f"   Overall Risk: {metadata.get('overall_risk_score', 'N/A')} ({metadata.get('overall_risk_severity', 'N/A')})\n"
                            historical_context += f"   Financial: {metadata.get('financial_risk_score', 'N/A')}, Legal: {metadata.get('legal_risk_score', 'N/A')}\n"
        except Exception as e:
            print(f"⚠️ Could not retrieve historical risk context: {e}")
        
        # Initialize risk scoring agent
        risk_agent = RiskScoringAgent(gemini_api_key)
        
        # Score the lease agreement
        risk_assessment = risk_agent.score_lease_agreement(
            full_pdf_text=full_pdf_text,
            historical_context=historical_context,
            timestamp=timestamp,
            pdf_pages=pdf_pages  # NEW: Pass pages for position extraction
        )
        
        # Convert to dict for JSON serialization
        risk_assessment_dict = RiskScoringAgent.to_dict(risk_assessment)
        
        print("✅ 3-step pipeline complete!")
        return classification_results, analysis_results, risk_assessment_dict
        
    except Exception as e:
        error_msg = f"⚠️ Error during risk scoring: {str(e)}"
        print(f"❌ Risk scoring error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty risk assessment on error (graceful degradation)
        return classification_results, analysis_results, {}


def build_conversation_context(history: List[Tuple[str, str]], max_history: int = 5) -> str:
    """
    Convert history format to readable context string.

    Args:
        history: List of (user_msg, assistant_msg) tuples
        max_history: Maximum number of past exchanges to include

    Returns:
        Formatted conversation history string
    """
    if not history:
        return ""

    # Limit to recent exchanges to avoid token overflow
    recent_history = history[-max_history:]

    context_parts = []
    for user_msg, bot_msg in recent_history:
        if user_msg:  # Only add if user message exists
            context_parts.append(f"User: {user_msg}")
        if bot_msg:  # Only add if bot message exists
            context_parts.append(f"Assistant: {bot_msg}")

    return "\n".join(context_parts)


def format_retrieved_clauses(similar_clauses: List[Dict[str, Any]]) -> str:
    """
    Format retrieved content (pages or clauses) for LLM context.

    Args:
        similar_clauses: List of clause/page dicts from retrieve_similar_clauses()

    Returns:
        Formatted string with content information
    """
    if not similar_clauses:
        return "No relevant content found in the knowledge base."

    formatted_parts = []
    for i, item in enumerate(similar_clauses, 1):
        similarity_score = 1 - item['distance']
        metadata = item['metadata']

        # Handle both old clause-based and new page-based storage
        is_page = metadata.get('type') == 'pdf_page'

        if is_page:
            formatted_parts.append(
                f"[Document {i}]\n"
                f"Text: {item['text'][:500]}{'...' if len(item['text']) > 500 else ''}\n"
                f"Source: {metadata.get('source_doc', 'Unknown')} (Page {metadata.get('page', 'N/A')})\n"
                f"Relevance: {similarity_score:.2f}\n"
            )
        else:
            # Old clause-based format (for backward compatibility)
            formatted_parts.append(
                f"[Clause {i}]\n"
                f"Text: {item['text']}\n"
                f"Type: {metadata.get('label', 'Unknown')}\n"
                f"Source: {metadata.get('source_doc', 'Unknown')}\n"
                f"Confidence: {metadata.get('confidence', 0):.2f}\n"
                f"Relevance: {similarity_score:.2f}\n"
            )

    return "\n".join(formatted_parts)


def construct_conversational_prompt(
    user_question: str,
    conversation_history: str,
    retrieved_clauses: str,
    kb_stats: Dict[str, Any]
) -> str:
    """Construct the full prompt for the LLM."""

    prompt = f"""KNOWLEDGE BASE: {kb_stats['total_clauses']} clauses from processed lease agreements

"""

    if conversation_history:
        prompt += f"""CONVERSATION HISTORY:
{conversation_history}

"""

    prompt += f"""RETRIEVED RELEVANT CLAUSES:
{retrieved_clauses}

CURRENT QUESTION: {user_question}

Please provide a helpful answer based on the retrieved clauses above. If the conversation history is relevant, maintain continuity with previous responses."""

    return prompt


def generate_chat_response(
    message: str,
    history: List[Tuple[str, str]],
    gemini_api_key: str,
    clause_store,  # ClauseStore instance
    top_k: int = 5
) -> Tuple[str, List[str]]:
    """
    Generate conversational response using RAG.

    Args:
        message: User's current question
        history: List of (user_msg, assistant_msg) tuples
        gemini_api_key: Google Gemini API key
        clause_store: ClauseStore instance
        top_k: Number of similar clauses to retrieve

    Returns:
        Tuple of (response_text, sources_list)
    """
    # Validation
    if not gemini_api_key or gemini_api_key.strip() == "":
        raise ValueError("Valid Gemini API key is required")

    # Check knowledge base
    stats = clause_store.get_statistics()
    if stats['total_clauses'] < 3:
        return (
            "📭 The knowledge base is empty or has too few clauses. "
            "Please process some PDF documents first.",
            []
        )

    # Retrieve relevant clauses
    similar_clauses = clause_store.retrieve_similar_clauses(
        query=message,
        top_k=int(top_k),
        label_filter=None  # Search across ALL labels
    )

    if not similar_clauses:
        return (
            f"🔍 I couldn't find any clauses relevant to your question. "
            f"The knowledge base contains {stats['total_clauses']} clauses. "
            f"Try rephrasing or ask about a different topic.",
            []
        )

    # Build context
    conversation_context = build_conversation_context(history)
    context_text = format_retrieved_clauses(similar_clauses)

    # Construct prompt
    prompt = construct_conversational_prompt(
        user_question=message,
        conversation_history=conversation_context,
        retrieved_clauses=context_text,
        kb_stats=stats
    )

    # Call Gemini LLM
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Combine system prompt with user prompt (Gemini doesn't have separate system messages)
    full_prompt = f"""{CONVERSATIONAL_SYSTEM_PROMPT}

---

{prompt}"""

    response = model.generate_content(
        full_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.5,
            max_output_tokens=2000  # Increased for detailed responses
        )
    )

    response_text = response.text

    # Extract source documents
    sources = list(set([c['metadata'].get('source_doc', 'Unknown') for c in similar_clauses[:3]]))

    return response_text, sources
