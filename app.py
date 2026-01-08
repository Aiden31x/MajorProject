"""
ClauseCraft: AI-Powered Lease Agreement Analyzer with RAG
Main application file with Gradio UI and processing pipeline
"""
import os
from datetime import datetime
from collections import Counter
import gradio as gr
import google.generativeai as genai

# Import from new modules
from config import GEMINI_API_KEY, GEMINI_MODEL, APP_TITLE, APP_DESCRIPTION, SERVER_NAME, SERVER_PORT
from pdf_utils import extract_text_by_pages
from rag import ClauseStore

# ================================================================
# Initialize Components
# ================================================================
print("=" * 60)
print("🏢 ClauseCraft: AI-Powered Lease Agreement Analyzer with RAG")
print("=" * 60)

try:
    print("\n📦 Initializing RAG system...")
    clause_store = ClauseStore()

    print("\n✅ All systems ready!")
    print("=" * 60 + "\n")
except Exception as e:
    print(f"❌ Error initializing RAG system: {e}")
    exit(1)

# ================================================================
# LLM-Based Clause Extraction and Analysis with RAG Grounding
# ================================================================
def extract_and_analyze_with_llm(full_pdf_text, source_doc, gemini_api_key):
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

    # Prompt for extraction and classification
    extraction_prompt = f"""You are a legal expert analyzing a lease agreement. Your task is to:

1. Extract and list ALL important clauses from this lease agreement
2. Classify each clause into one of these categories:
   - redflag (unfair or risky terms)
   - rent_review_date
   - term_of_payment
   - notice_period
   - lessor (landlord information)
   - lessee (tenant information)
   - start_date / end_date
   - leased_space
   - extension_period
   - vat
   - designated_use
   - other (if none of the above apply)

3. For each clause, provide:
   - The exact text of the clause
   - Its classification
   - A brief explanation (especially for red flags)

LEASE AGREEMENT TEXT:
{pdf_text_truncated}
{historical_context}

Please extract and classify clauses in the following markdown format:

## Extracted Clauses

### 1. [Classification]
**Clause:** [exact text]
**Explanation:** [brief explanation, especially for red flags]

### 2. [Classification]
...

After listing ALL clauses, provide:

## Summary Analysis
- Key terms (rent, deposit, duration, parties)
- Total red flags found
- Main concerns
- Recommendations for tenant

Please be thorough and extract ALL important clauses from the document. Use clear formatting with markdown."""

    try:
        print("🤖 Using Gemini to extract and classify clauses...")
        response = model.generate_content(
            extraction_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,  # Lower temperature for more consistent extraction
                max_output_tokens=8000  # Increased from 2000 to allow full lease analysis
            )
        )

        # Check if response was blocked or incomplete
        if not response.text:
            if hasattr(response, 'prompt_feedback'):
                return f"⚠️ Response blocked: {response.prompt_feedback}", ""
            return "⚠️ Empty response from Gemini", ""

        llm_response = response.text

        # Check if response was truncated
        if hasattr(response, 'candidates') and len(response.candidates) > 0:
            finish_reason = response.candidates[0].finish_reason
            if finish_reason and 'MAX_TOKENS' in str(finish_reason):
                llm_response += "\n\n⚠️ **Note:** Response was truncated due to length. Consider uploading a shorter document or processing in sections."

        # Return both as classification results and analysis
        return llm_response, llm_response

    except Exception as e:
        error_msg = f"⚠️ Error during Gemini extraction: {str(e)}"
        print(f"Full error: {e}")
        return error_msg, error_msg

# ================================================================
# Conversational RAG Query Interface
# ================================================================

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


def build_conversation_context(history: list, max_history: int = 5) -> str:
    """
    Convert Gradio history format to readable context string.

    Args:
        history: List of [user_msg, bot_msg] pairs from ChatInterface
        max_history: Maximum number of past exchanges to include

    Returns:
        Formatted conversation history string
    """
    if not history:
        return ""

    # Limit to recent exchanges to avoid token overflow
    recent_history = history[-max_history:]

    context_parts = []
    for item in recent_history:
        # Handle different formats: [user, bot] or just messages
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            user_msg = item[0]
            bot_msg = item[1]
            if user_msg:  # Only add if user message exists
                context_parts.append(f"User: {user_msg}")
            if bot_msg:  # Only add if bot message exists
                context_parts.append(f"Assistant: {bot_msg}")
        elif isinstance(item, dict):
            # Handle dict format if that's what Gradio uses
            if 'user' in item and item['user']:
                context_parts.append(f"User: {item['user']}")
            if 'assistant' in item and item['assistant']:
                context_parts.append(f"Assistant: {item['assistant']}")

    return "\n".join(context_parts)


def format_retrieved_clauses(similar_clauses: list) -> str:
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


def get_kb_statistics_display() -> str:
    """Generate markdown display of knowledge base statistics."""
    try:
        stats = clause_store.get_statistics()

        # Count red flags (sample approach)
        redflag_count = 0
        try:
            redflags = clause_store.get_clauses_by_label('redflag', limit=1000)
            redflag_count = len(redflags) if redflags else 0
        except:
            pass

        return f"""### 📊 Knowledge Base Statistics
- **Total Clauses:** {stats['total_clauses']}
- **Red Flags Detected:** {redflag_count}
- **Status:** {'Ready for queries' if stats['total_clauses'] > 0 else 'Empty - process PDFs first'}

*Ask me anything about your lease clauses!*
"""
    except Exception as e:
        return f"### 📊 Knowledge Base Statistics\n*Unable to load statistics: {str(e)}*"


def construct_conversational_prompt(
    user_question: str,
    conversation_history: str,
    retrieved_clauses: str,
    kb_stats: dict
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


def handle_conversational_query(
    message: str,
    history: list,
    gemini_api_key: str,
    top_k: int = 5
) -> str:
    """
    Handle conversational queries about the lease clause knowledge base.

    Args:
        message: User's current question
        history: List of [user_msg, assistant_msg] pairs (managed by ChatInterface)
        gemini_api_key: Google Gemini API key
        top_k: Number of similar clauses to retrieve

    Returns:
        Assistant's response as string
    """
    # Validation
    if not gemini_api_key or gemini_api_key.strip() == "":
        return "⚠️ Please provide a valid Gemini API key in the settings below."

    # Check knowledge base
    try:
        stats = clause_store.get_statistics()
        if stats['total_clauses'] < 3:
            return ("📭 The knowledge base is empty or has too few clauses. "
                    "Please process some PDF documents in the 'PDF Analysis' tab first.")
    except Exception as e:
        return f"⚠️ Error accessing knowledge base: {str(e)}"

    # Retrieve relevant clauses
    try:
        similar_clauses = clause_store.retrieve_similar_clauses(
            query=message,
            top_k=int(top_k),
            label_filter=None  # Search across ALL labels
        )
    except Exception as e:
        return f"⚠️ Error retrieving clauses: {str(e)}"

    if not similar_clauses:
        return f"🔍 I couldn't find any clauses relevant to your question. The knowledge base contains {stats['total_clauses']} clauses. Try rephrasing or ask about a different topic."

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
    try:
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

        # Add source information
        response_text = response.text
        sources = set([c['metadata'].get('source_doc', 'Unknown') for c in similar_clauses[:3]])
        response_text += f"\n\n---\n📚 *Sources: {', '.join(sources)}*"

        return response_text

    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}\n\nPlease check your API key and try again."


# ================================================================
# Main Processing Pipeline (Enhanced with RAG)
# ================================================================
def process_lease_agreement(pdf_file, gemini_api_key, progress=gr.Progress()):
    """
    NEW Pipeline: Extract Pages → Store in RAG → LLM Extract & Classify → Analyze

    Steps:
    1. Extract text from PDF by pages (preserves context)
    2. Store full pages in RAG knowledge base
    3. Use Gemini LLM to extract and classify clauses from full document
    4. Generate analysis with RAG grounding
    """

    if pdf_file is None:
        return "❌ Please upload a PDF file", ""

    if not gemini_api_key or gemini_api_key.strip() == "":
        return "❌ Please provide a valid Gemini API key", ""

    try:
        # Handle file path - Gradio returns the file path
        pdf_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file

        # Step 1: Extract text from PDF by pages
        progress(0.2, desc="Extracting text from PDF...")
        pages = extract_text_by_pages(pdf_path)

        if not pages or len(pages) == 0:
            return "❌ Could not extract text from PDF. Please ensure it's a valid PDF with text content.", ""

        # Combine pages into full text for LLM analysis
        full_pdf_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in pages])

        if len(full_pdf_text) < 10:
            return "❌ PDF appears to be empty or unreadable.", ""

        # Step 2: Store pages in RAG system
        progress(0.4, desc=f"Storing {len(pages)} pages in knowledge base...")
        timestamp = datetime.now().isoformat()
        source_doc = os.path.basename(pdf_path)

        try:
            clause_store.add_pdf_pages(pages, source_doc, timestamp)
            rag_status = "✅ Yes"
            total_in_kb = clause_store.get_statistics()['total_clauses']
        except Exception as e:
            print(f"⚠️ Error storing in RAG: {e}")
            rag_status = "⚠️ Error"
            total_in_kb = 0

        # Step 3 & 4: Use Gemini to extract, classify, and analyze
        progress(0.6, desc="Using Gemini to extract and classify clauses...")
        classification_results, analysis_results = extract_and_analyze_with_llm(
            full_pdf_text,
            source_doc,
            gemini_api_key
        )

        # Generate summary statistics
        progress(0.9, desc="Preparing results...")
        results_md = f"""# 📄 {source_doc}

## 📊 Document Statistics

- **Total Pages:** {len(pages)}
- **Total Characters:** {len(full_pdf_text):,}
- **Stored in Knowledge Base:** {rag_status} ({total_in_kb} total documents/pages)
- **Analysis Method:** LLM-based extraction with full context
- **RAG Enhancement:** {'✅ Active' if total_in_kb > len(pages) else '⏳ First document (no historical context yet)'}

---

{classification_results}
"""

        progress(1.0, desc="Complete!")

        final_analysis = f"# 📑 AI-Powered Lease Analysis (RAG-Enhanced)\n\n{analysis_results}"

        return results_md, final_analysis

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg, ""

# ================================================================
# Gradio Interface
# ================================================================
with gr.Blocks(title="ClauseCraft") as demo:

    gr.Markdown(f"# {APP_TITLE}\n\n{APP_DESCRIPTION}")

    with gr.Tabs():
        # ===== TAB 1: Existing PDF Analysis =====
        with gr.Tab("📄 PDF Analysis"):
            with gr.Row():
                with gr.Column(scale=1):
                    pdf_input = gr.File(
                        label="📄 Upload Lease Agreement (PDF)",
                        file_types=[".pdf"]
                    )

                    api_key_input = gr.Textbox(
                        label="🔑 Gemini API Key",
                        type="password",
                        value=GEMINI_API_KEY,
                        placeholder="Enter your Gemini API key"
                    )

                    analyze_btn = gr.Button("🔍 Analyze Lease Agreement", variant="primary", size="lg")

                    gr.Markdown(
                        """
                        ### 📌 How to use:
                        1. Upload your lease agreement PDF
                        2. Enter your Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
                        3. Click "Analyze Lease Agreement"
                        4. Review the LLM-extracted clauses and analysis

                        ### 🆕 Enhanced with RAG & Gemini:
                        - PDFs are stored page-by-page in the knowledge base
                        - Gemini extracts and classifies clauses from full document context
                        - Historical lease agreements provide context for better analysis
                        - More accurate than regex-based splitting
                        """
                    )

            with gr.Row():
                with gr.Column(scale=1):
                    classification_output = gr.Markdown(label="Classification Results")

                with gr.Column(scale=1):
                    analysis_output = gr.Markdown(label="AI Analysis")

            analyze_btn.click(
                fn=process_lease_agreement,
                inputs=[pdf_input, api_key_input],
                outputs=[classification_output, analysis_output]
            )

            gr.Markdown(
                """
                ---
                ### 🏷️ Clause Types Extracted by Gemini:
                Red Flags • Rent Terms • Payment Terms • Notice Period • Lessor/Lessee •
                Leased Space • Extension Period • VAT • Designated Use • Start/End Dates • and more...

                ### 🔬 RAG System Status:
                - **Analysis Method:** LLM-based extraction (Google Gemini)
                - **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2
                - **Vector Database:** ChromaDB (local persistence)
                - **Storage:** Page-by-page with full context
                - **Knowledge Base:** Growing with each processed document
                """
            )

        # ===== TAB 2: NEW - Conversational Query Interface =====
        with gr.Tab("💬 Query Knowledge Base"):
            gr.Markdown("""
            ## Ask Questions About Your Lease Agreements

            Query the knowledge base containing all processed lease agreements (stored page-by-page).
            The AI will retrieve relevant document sections and provide conversational, context-aware answers.
            """)

            # Knowledge Base Statistics
            with gr.Row():
                stats_display = gr.Markdown(value=get_kb_statistics_display())

            # Main Chat Interface
            chat_interface = gr.ChatInterface(
    fn=handle_conversational_query,
    chatbot=gr.Chatbot(
        height=500,
        render_markdown=True,

    ),
    textbox=gr.Textbox(
        placeholder="Ask me anything about lease clauses...",
        container=False,
        scale=7
    ),
    additional_inputs=[
        gr.Textbox(
            label="🔑 Gemini API Key",
            type="password",
            value=GEMINI_API_KEY,
            placeholder="Enter your Gemini API key"
        ),
        gr.Slider(
            label="Number of relevant documents to retrieve",
            minimum=3,
            maximum=10,
            value=5,
            step=1,
            info="More documents = better context but slower responses"
        )
    ],
 
)


            # Example queries
            gr.Examples(
                examples=[
                    "What are common red flags in lease agreements?",
                    "Show me examples of unfair rent escalation clauses",
                    "What should I look for in notice period clauses?",
                    "Are there any concerning VAT-related clauses?",
                    "What are typical lease extension terms?",
                    "Summarize the most common lessor obligations"
                ],
                inputs=chat_interface.textbox,
                label="💡 Example Questions"
            )

            gr.Markdown("""
            ---
            ### 💡 Tips:
            - Ask follow-up questions - the assistant remembers conversation context
            - Be specific about what you want to know
            - Questions can be about specific clause types or general patterns
            - The system searches across all stored lease clauses
            """)

# ================================================================
# Launch App
# ================================================================
if __name__ == "__main__":
    print("\n🌐 Starting Gradio interface...")
    print(f"📍 Access the app at: http://{SERVER_NAME}:{SERVER_PORT}")
    print("\n Press Ctrl+C to stop the server\n")

    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        theme=gr.themes.Soft(),
        debug=True
    )
