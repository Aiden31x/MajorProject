"""
Configuration module for ClauseCraft
Contains all constants, API keys, and settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ================================================================
# Model & API Configuration
# ================================================================
MODEL_PATH = os.getenv("MODEL_PATH", "/Users/aiden/ClauseCraft(Minor)/9epochs-90 (1)")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ================================================================
# RAG Configuration
# ================================================================
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K_SIMILAR_CLAUSES = int(os.getenv("TOP_K_SIMILAR_CLAUSES", "5"))
MIN_SIMILARITY_THRESHOLD = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.6"))

# ================================================================
# Lease Clause Label Mapping (26 Classes)
# ================================================================
LEASE_LABEL_MAP = {
    0: 'expiration_date_of_lease',
    1: 'clause_number',
    2: 'leased_space',
    3: 'general_terms',
    4: 'redflags',
    5: 'lessee',
    6: 'notice_period',
    7: 'redflag',
    8: 'definition_number',
    9: 'sub_clause_number',
    10: 'vat',
    11: 'type_lease',
    12: 'rent_review_date',
    13: 'definition',
    14: 'clause_title',
    15: 'Agreement_Type',
    16: 'end_date',
    17: 'signing_date',
    18: 'annex',
    19: 'sub_clause_title',
    20: 'term_of_payment',
    21: 'indexation_rent',
    22: 'designated_use',
    23: 'lessor',
    24: 'start_date',
    25: 'extension_period'
}

# ================================================================
# UI Configuration
# ================================================================
APP_TITLE = "ClauseCraft: AI-Powered Lease Agreement Analyzer"
APP_DESCRIPTION = """
Upload your lease agreement PDF and get instant AI-powered analysis with clause classification and risk assessment.
"""
SERVER_NAME = os.getenv("SERVER_NAME", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "7860"))
