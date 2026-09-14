"""PDF text extraction using PyMuPDF and pdfplumber

Handles both text-based and scanned PDFs.
For scanned PDFs, falls back to Claude vision OCR.
"""

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber

from app.core.claude_client import get_claude_client


def extract_text_pymupdf(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fast, good for standard PDFs)

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    doc = fitz.open(pdf_path)
    text_parts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()
    return "\n\n".join(text_parts)


def extract_text_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (better table extraction)

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

    return "\n\n".join(text_parts)


def is_scanned_pdf(pdf_path: str, sample_pages: int = 3) -> bool:
    """Check if PDF is likely scanned (image-based) by testing text extraction

    Args:
        pdf_path: Path to PDF file
        sample_pages: Number of pages to sample

    Returns:
        True if PDF appears to be scanned
    """
    doc = fitz.open(pdf_path)
    pages_to_check = min(sample_pages, len(doc))

    total_text_length = 0
    for page_num in range(pages_to_check):
        page = doc[page_num]
        text = page.get_text().strip()
        total_text_length += len(text)

    doc.close()

    # If average text per page is very low, likely scanned
    avg_text_per_page = total_text_length / pages_to_check
    return avg_text_per_page < 50


def extract_text_from_scanned_pdf(pdf_path: str) -> str:
    """Extract text from scanned PDF using Claude vision OCR

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text via OCR
    """
    # Convert PDF pages to images and OCR with Claude
    doc = fitz.open(pdf_path)
    text_parts = []
    client = get_claude_client()

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Render page to image
        pix = page.get_pixmap(dpi=150)
        img_path = f"/tmp/pdf_page_{page_num}.png"
        pix.save(img_path)

        # OCR with Claude
        try:
            ocr_text = client.extract_text_from_image(
                img_path,
                prompt="Extract all text from this PDF page. Preserve formatting and structure."
            )
            if ocr_text.strip():
                text_parts.append(f"--- Page {page_num + 1} (OCR) ---\n{ocr_text}")
        except Exception as e:
            text_parts.append(f"--- Page {page_num + 1} (OCR failed: {e}) ---")

    doc.close()
    return "\n\n".join(text_parts)


def parse_pdf(pdf_path: str, force_ocr: bool = False) -> str:
    """Parse PDF and extract text (auto-detects scanned PDFs)

    Args:
        pdf_path: Path to PDF file
        force_ocr: Force OCR even if text extraction works

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is invalid or empty
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    # Check if scanned PDF
    if force_ocr or is_scanned_pdf(pdf_path):
        return extract_text_from_scanned_pdf(pdf_path)

    # Try PyMuPDF first (faster)
    text = extract_text_pymupdf(pdf_path)

    # If PyMuPDF fails, try pdfplumber
    if not text or len(text.strip()) < 100:
        text = extract_text_pdfplumber(pdf_path)

    # If still no text, treat as scanned
    if not text or len(text.strip()) < 50:
        text = extract_text_from_scanned_pdf(pdf_path)

    if not text.strip():
        raise ValueError(f"No text content found in PDF: {pdf_path}")

    return text
