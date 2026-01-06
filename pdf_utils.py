"""
PDF processing utilities for lease agreements
Handles PDF text extraction and clause segmentation
"""
import re
import PyPDF2


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF file.

    Args:
        pdf_file: Either a file path (string) or file object from Gradio

    Returns:
        Extracted text as string

    Raises:
        Exception: If PDF cannot be read or is empty
    """
    text = ""

    # Handle both file path (string) and file object
    if isinstance(pdf_file, str):
        # It's a file path
        with open(pdf_file, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    else:
        # It's a file object
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() + "\n"

    return text


def split_into_clauses(text: str) -> list[str]:
    """
    Split text into individual clauses using regex patterns.

    The splitting strategy:
    - Splits on period or semicolon followed by whitespace
    - Splits on multiple newlines
    - Removes empty clauses
    - Strips whitespace from each clause

    Args:
        text: Raw text extracted from PDF

    Returns:
        List of clause strings
    """
    # Split on sentence endings or multiple newlines
    clauses = re.split(r'(?<=[.;])\s+|\n+', text)

    # Clean up clauses
    clauses = [c.strip() for c in clauses if c.strip()]

    return clauses


def preprocess_clause_text(text: str) -> str:
    """
    Clean and normalize clause text for better embedding quality.

    Preprocessing steps:
    - Remove excessive whitespace
    - Normalize line breaks
    - Remove special characters that don't add meaning

    Args:
        text: Raw clause text

    Returns:
        Cleaned clause text
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")

    return text
