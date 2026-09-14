"""DOCX text extraction using python-docx

Extracts text from Word documents including paragraphs and tables.
"""

from pathlib import Path
from docx import Document


def parse_docx(docx_path: str) -> str:
    """Parse DOCX file and extract text content

    Args:
        docx_path: Path to DOCX file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If DOCX file doesn't exist
        ValueError: If DOCX is invalid or empty
    """
    path = Path(docx_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    if path.suffix.lower() not in [".docx", ".doc"]:
        raise ValueError(f"Not a DOCX file: {docx_path}")

    doc = Document(docx_path)
    text_parts = []

    # Extract paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    # Extract tables
    for table in doc.tables:
        table_text = []
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells)
            if row_text.strip():
                table_text.append(row_text)

        if table_text:
            text_parts.append("\n[TABLE]\n" + "\n".join(table_text) + "\n[/TABLE]\n")

    text = "\n\n".join(text_parts)

    if not text.strip():
        raise ValueError(f"No text content found in DOCX: {docx_path}")

    return text
