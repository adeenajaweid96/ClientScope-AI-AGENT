"""Normalizer - converts all input types to unified text+image format

Output format:
{
    "text": "combined text from all sources",
    "images": [{"path": "...", "source": "..."}],
    "source_type": "pdf|docx|image|text",
    "metadata": {...}
}
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

from app.preprocessing.pdf_parser import parse_pdf
from app.preprocessing.docx_parser import parse_docx
from app.preprocessing.vision_extractor import extract_text_from_image


class SourceType(str, Enum):
    """Input source types"""
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    TEXT = "text"
    MIXED = "mixed"


class NormalizedInput:
    """Normalized input representation"""

    def __init__(
        self,
        text: str,
        source_type: SourceType,
        images: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.source_type = source_type
        self.images = images or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "source_type": self.source_type.value,
            "images": self.images,
            "metadata": self.metadata
        }


def normalize_pdf(pdf_path: str) -> NormalizedInput:
    """Normalize PDF input

    Args:
        pdf_path: Path to PDF file

    Returns:
        NormalizedInput with extracted text
    """
    text = parse_pdf(pdf_path)
    metadata = {
        "original_filename": Path(pdf_path).name,
        "file_size": Path(pdf_path).stat().st_size
    }

    return NormalizedInput(
        text=text,
        source_type=SourceType.PDF,
        metadata=metadata
    )


def normalize_docx(docx_path: str) -> NormalizedInput:
    """Normalize DOCX input

    Args:
        docx_path: Path to DOCX file

    Returns:
        NormalizedInput with extracted text
    """
    text = parse_docx(docx_path)
    metadata = {
        "original_filename": Path(docx_path).name,
        "file_size": Path(docx_path).stat().st_size
    }

    return NormalizedInput(
        text=text,
        source_type=SourceType.DOCX,
        metadata=metadata
    )


def normalize_image(image_path: str) -> NormalizedInput:
    """Normalize image input

    Args:
        image_path: Path to image file

    Returns:
        NormalizedInput with OCR text
    """
    text = extract_text_from_image(image_path)
    metadata = {
        "original_filename": Path(image_path).name,
        "file_size": Path(image_path).stat().st_size
    }

    return NormalizedInput(
        text=text,
        source_type=SourceType.IMAGE,
        images=[{"path": image_path, "source": "upload"}],
        metadata=metadata
    )


def normalize_text(text: str, source_label: str = "pasted_text") -> NormalizedInput:
    """Normalize pasted text input

    Args:
        text: Raw text content
        source_label: Label for the text source

    Returns:
        NormalizedInput with text
    """
    metadata = {
        "source_label": source_label,
        "character_count": len(text)
    }

    return NormalizedInput(
        text=text,
        source_type=SourceType.TEXT,
        metadata=metadata
    )


def normalize_file(file_path: str) -> NormalizedInput:
    """Auto-detect file type and normalize

    Args:
        file_path: Path to file

    Returns:
        NormalizedInput with extracted content

    Raises:
        ValueError: If file type is unsupported
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return normalize_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return normalize_docx(file_path)
    elif suffix in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return normalize_image(file_path)
    elif suffix in [".txt", ".md"]:
        text = path.read_text(encoding="utf-8")
        return normalize_text(text, source_label=path.name)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def normalize_multiple_files(file_paths: List[str]) -> NormalizedInput:
    """Normalize multiple files into a single input

    Args:
        file_paths: List of file paths

    Returns:
        NormalizedInput with combined content
    """
    if not file_paths:
        raise ValueError("No files provided")

    if len(file_paths) == 1:
        return normalize_file(file_paths[0])

    # Process each file
    normalized_inputs = []
    for file_path in file_paths:
        try:
            normalized = normalize_file(file_path)
            normalized_inputs.append(normalized)
        except Exception as e:
            # Include error in output
            normalized_inputs.append(
                NormalizedInput(
                    text=f"[Error processing {Path(file_path).name}: {e}]",
                    source_type=SourceType.TEXT,
                    metadata={"error": str(e), "filename": Path(file_path).name}
                )
            )

    # Combine all inputs
    combined_text_parts = []
    combined_images = []
    combined_metadata = {"files": []}

    for idx, normalized in enumerate(normalized_inputs):
        combined_text_parts.append(
            f"\n\n--- File {idx + 1}: {normalized.metadata.get('original_filename', 'unknown')} ---\n"
            f"{normalized.text}"
        )
        combined_images.extend(normalized.images)
        combined_metadata["files"].append(normalized.metadata)

    combined_text = "\n".join(combined_text_parts)

    return NormalizedInput(
        text=combined_text,
        source_type=SourceType.MIXED,
        images=combined_images,
        metadata=combined_metadata
    )
