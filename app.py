"""
ClauseCraft: AI-Powered Lease Agreement Analyzer with RAG
Main application file with Gradio UI and processing pipeline
"""
import os
from datetime import datetime
from collections import Counter
import gradio as gr
from groq import Groq

# Import from new modules
from config import GROQ_API_KEY, APP_TITLE, APP_DESCRIPTION, SERVER_NAME, SERVER_PORT
from classifier import LeaseLegalClassifier
from pdf_utils import extract_text_from_pdf, split_into_clauses
from rag import ClauseStore

# ================================================================
# Initialize Components
# ================================================================
print("=" * 60)
print("🏢 ClauseCraft: AI-Powered Lease Agreement Analyzer with RAG")
print("=" * 60)

try:
    print("\n📦 Initializing classifier...")
    classifier = LeaseLegalClassifier()

    print("\n📦 Initializing RAG system...")
    clause_store = ClauseStore()

    print("\n✅ All systems ready!")
    print("=" * 60 + "\n")
except Exception as e:
    print(f"❌ Error initializing components: {e}")
    print("Please ensure your model files are in the correct directory")
    exit(1)

# ================================================================
# Enhanced LLM Analysis with RAG Grounding
# ================================================================
def analyze_with_grounded_llm(clauses_with_preds, source_doc, groq_api_key):
    """
    Enhanced LLM analysis with RAG-based evidence grounding.

    This function retrieves similar historical clauses from the knowledge base
    to provide context and evidence for the LLM analysis.

    Args:
        clauses_with_preds: List of classified clauses
        source_doc: Source document filename
        groq_api_key: Groq API key for LLM

    Returns:
        Markdown-formatted analysis with grounded insights
    """
    client = Groq(api_key=groq_api_key)

    # Limit to first 40 clauses to avoid token limits
    limited_clauses = clauses_with_preds[:40]

    # Count red flags
    redflags = [c for c in clauses_with_preds if 'redflag' in c['predicted_class'].lower()]

    # For each red flag, find similar historical clauses (GROUNDING WITH RAG)
    redflag_context = []
    if redflags and clause_store.get_statistics()['total_clauses'] > 10:
        print(f"🔍 Retrieving similar clauses for {len(redflags)} red flags...")

        for rf in redflags[:5]:  # Limit to first 5 red flags
            try:
                similar = clause_store.retrieve_similar_clauses(
                    query=rf['clause'],
                    top_k=3,
                    label_filter="redflag"  # Only get similar red flags
                )

                if similar:
                    redflag_context.append({
                        "current_redflag": rf['clause'][:200],
                        "similar_historical": [
                            {
                                "text": s['text'][:150],
                                "source": s['metadata'].get('source_doc', 'Unknown'),
                                "similarity": 1 - s['distance']  # Convert distance to similarity
                            }
                            for s in similar
                        ]
                    })
            except Exception as e:
                print(f"⚠️ Could not retrieve similar clauses: {e}")

    # Build prompt with classified clauses
    text_blocks = []
    for item in limited_clauses:
        clause_text = item['clause'][:200] + "..." if len(item['clause']) > 200 else item['clause']
        text_blocks.append(
            f"Clause: {clause_text}\n"
            f"Label: {item['predicted_class']}\n"
            f"Confidence: {item['confidence']:.2f}"
        )

    input_text = "\n\n".join(text_blocks)

    # Add historical context if available (THIS IS THE RAG GROUNDING)
    evidence_text = ""
    if redflag_context:
        evidence_text = "\n\n--- HISTORICAL EVIDENCE FROM KNOWLEDGE BASE ---\n"
        evidence_text += f"Found {len(redflag_context)} red flags with historical matches:\n\n"

        for i, ctx in enumerate(redflag_context, 1):
            evidence_text += f"\n{i}. Current Red Flag:\n"
            evidence_text += f"   {ctx['current_redflag']}\n\n"
            evidence_text += f"   Similar past cases ({len(ctx['similar_historical'])} found):\n"
            for j, hist in enumerate(ctx['similar_historical'], 1):
                evidence_text += f"   {j}. [{hist['source']}] {hist['text']} (Similarity: {hist['similarity']:.2f})\n"

    # Construct grounded prompt
    prompt = f"""
You are a legal assistant analyzing a lease agreement. Here are {len(limited_clauses)} classified clauses:

{input_text}

IMPORTANT: There are {len(redflags)} clauses marked as potential red flags in the full document.
{evidence_text}

Tasks:
1. Summarize the key terms you can identify (Rent, Deposit, Duration, Parties, Use, etc.)
2. List the red flag clauses and explain risks
   - If historical evidence is provided above, use it to contextualize the risks
   - Compare current clauses with similar historical patterns
3. Give 2-3 recommendations for the tenant based on evidence
4. Keep response under 500 words

Format in markdown with clear sections.
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )

        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error generating analysis: {str(e)}"

# ================================================================
# Main Processing Pipeline (Enhanced with RAG)
# ================================================================
def process_lease_agreement(pdf_file, groq_api_key, progress=gr.Progress()):
    """
    Main pipeline: Extract → Classify → Store in RAG → Analyze with Grounding

    Steps:
    1. Extract text from PDF
    2. Split into clauses
    3. Classify each clause using fine-tuned ALBERT
    4. Store clauses in RAG knowledge base
    5. Retrieve relevant context for analysis
    6. Generate grounded LLM analysis
    """

    if pdf_file is None:
        return "❌ Please upload a PDF file", ""

    if not groq_api_key or groq_api_key.strip() == "":
        return "❌ Please provide a valid Groq API key", ""

    try:
        # Handle file path - Gradio returns the file path
        pdf_path = pdf_file.name if hasattr(pdf_file, 'name') else pdf_file

        # Step 1: Extract text from PDF
        progress(0.2, desc="Extracting text from PDF...")
        pdf_text = extract_text_from_pdf(pdf_path)

        if not pdf_text or len(pdf_text) < 10:
            return "❌ Could not extract text from PDF. Please ensure it's a valid PDF with text content.", ""

        # Step 2: Split into clauses
        progress(0.3, desc="Splitting into clauses...")
        clauses = split_into_clauses(pdf_text)

        # Step 3: Classify each clause
        progress(0.4, desc=f"Classifying {len(clauses)} clauses...")
        clauses_with_preds = []

        for i, clause in enumerate(clauses):
            result = classifier.classify(clause)
            clauses_with_preds.append({
                "clause": clause,
                "predicted_class": result["predicted_class"],
                "confidence": result["confidence"]
            })

            if i % 10 == 0:
                progress((0.4 + 0.3 * i / len(clauses)), desc=f"Classifying clause {i+1}/{len(clauses)}...")

        # Step 4: Store in RAG system (NEW - THE KEY ENHANCEMENT)
        progress(0.7, desc="Storing clauses in knowledge base...")
        timestamp = datetime.now().isoformat()
        source_doc = os.path.basename(pdf_path)

        rag_clauses = []
        for i, item in enumerate(clauses_with_preds):
            rag_clauses.append({
                "clause_id": f"{source_doc}_CL_{i:03d}",
                "text": item["clause"],
                "label": item["predicted_class"],
                "confidence": item["confidence"],
                "source_doc": source_doc,
                "timestamp": timestamp
            })

        try:
            clause_store.add_clauses_batch(rag_clauses)
            rag_status = "✅ Yes"
        except Exception as e:
            print(f"⚠️ Error storing in RAG: {e}")
            rag_status = "⚠️ Error"

        # Step 5: Generate classification results
        progress(0.8, desc="Generating results...")
        label_counts = Counter([c['predicted_class'] for c in clauses_with_preds])

        results_md = "## 📊 Document Statistics\n\n"
        results_md += f"- **Total Clauses:** {len(clauses_with_preds)}\n"
        results_md += f"- **Red Flags Found:** {label_counts.get('redflag', 0) + label_counts.get('redflags', 0)}\n"
        results_md += f"- **Average Confidence:** {sum(c['confidence'] for c in clauses_with_preds) / len(clauses_with_preds):.2%}\n"
        results_md += f"- **Stored in Knowledge Base:** {rag_status} ({clause_store.get_statistics()['total_clauses']} total clauses)\n\n"

        results_md += "### 🏷️ Top Label Types:\n"
        for label, count in label_counts.most_common(5):
            results_md += f"- **{label}**: {count}\n"

        results_md += "\n## 📋 Classification Results\n\n"
        results_md += "| # | Clause Preview | Predicted Label | Confidence |\n"
        results_md += "|---|----------------|-----------------|------------|\n"

        for i, item in enumerate(clauses_with_preds[:30], 1):  # Show first 30
            clause_preview = item['clause'][:80] + "..." if len(item['clause']) > 80 else item['clause']
            conf_emoji = "🟢" if item['confidence'] > 0.8 else "🟡" if item['confidence'] > 0.6 else "🔴"
            results_md += f"| {i} | {clause_preview} | {item['predicted_class']} | {conf_emoji} {item['confidence']:.2f} |\n"

        if len(clauses_with_preds) > 30:
            results_md += f"\n*Showing 30 of {len(clauses_with_preds)} clauses*\n"

        # Step 6: Get RAG-enhanced LLM analysis
        progress(0.9, desc="Analyzing with AI (RAG-enhanced)...")
        llm_analysis = analyze_with_grounded_llm(clauses_with_preds, source_doc, groq_api_key)

        progress(1.0, desc="Complete!")

        final_analysis = f"# 📑 AI-Powered Lease Analysis (RAG-Enhanced)\n\n{llm_analysis}"

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
with gr.Blocks(theme=gr.themes.Soft(), title="ClauseCraft") as demo:
    gr.Markdown(f"# {APP_TITLE}\n\n{APP_DESCRIPTION}")

    with gr.Row():
        with gr.Column(scale=1):
            pdf_input = gr.File(
                label="📄 Upload Lease Agreement (PDF)",
                file_types=[".pdf"]
            )

            api_key_input = gr.Textbox(
                label="🔑 Groq API Key",
                type="password",
                value=GROQ_API_KEY,
                placeholder="Enter your Groq API key"
            )

            analyze_btn = gr.Button("🔍 Analyze Lease Agreement", variant="primary", size="lg")

            gr.Markdown(
                """
                ### 📌 How to use:
                1. Upload your lease agreement PDF
                2. Enter your Groq API key ([Get one here](https://console.groq.com))
                3. Click "Analyze Lease Agreement"
                4. Review the classification and AI analysis

                ### 🆕 RAG Enhancement:
                - Every processed clause is stored in the knowledge base
                - Similar historical clauses provide context for analysis
                - Red flags are compared against past risky clauses
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
        ### 🏷️ Supported Label Types:
        Start/End Dates • Rent Terms • Payment Terms • Red Flags • Lessor/Lessee •
        Leased Space • Notice Period • Extension Period • VAT • Designated Use • and more...

        ### 🔬 RAG System Status:
        - **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2
        - **Vector Database:** ChromaDB (local persistence)
        - **Knowledge Base:** Growing with each processed document
        """
    )

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
        debug=True
    )
