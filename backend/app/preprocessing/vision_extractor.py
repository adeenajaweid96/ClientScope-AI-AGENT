"""Image text extraction using Claude vision API

Handles screenshots, photos, and image-based documents.
"""

from pathlib import Path
from typing import List

from app.core.claude_client import get_claude_client


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image using Claude vision

    Args:
        image_path: Path to image file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image format is unsupported
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    supported_formats = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if path.suffix.lower() not in supported_formats:
        raise ValueError(f"Unsupported image format: {path.suffix}")

    client = get_claude_client()

    prompt = """Extract all text from this image. This may be:
- A screenshot of a conversation (email, chat, messages)
- A scanned document
- A photo of text
- A diagram with labels

Preserve the structure and formatting. If there's no text, describe what you see briefly."""

    text = client.extract_text_from_image(image_path, prompt=prompt)

    if not text.strip():
        raise ValueError(f"No text content extracted from image: {image_path}")

    return text


def extract_text_from_images(image_paths: List[str]) -> str:
    """Extract text from multiple images

    Args:
        image_paths: List of paths to image files

    Returns:
        Combined extracted text with image separators
    """
    text_parts = []

    for idx, image_path in enumerate(image_paths):
        try:
            text = extract_text_from_image(image_path)
            text_parts.append(f"--- Image {idx + 1} ({Path(image_path).name}) ---\n{text}")
        except Exception as e:
            text_parts.append(f"--- Image {idx + 1} (extraction failed: {e}) ---")

    return "\n\n".join(text_parts)
