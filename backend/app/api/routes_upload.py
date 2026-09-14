"""File upload routes

Handles uploading PDFs, DOCX files, screenshots, and pasted text.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.preprocessing.normalizer import (
    normalize_file,
    normalize_text,
    normalize_multiple_files,
    NormalizedInput
)

router = APIRouter(prefix="/upload", tags=["upload"])


class TextUploadRequest(BaseModel):
    """Request body for pasted text upload"""
    text: str
    label: Optional[str] = "pasted_text"


class NormalizedResponse(BaseModel):
    """Response with normalized content"""
    text: str
    source_type: str
    images: List[dict]
    metadata: dict


def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """Save uploaded file to disk

    Args:
        upload_file: FastAPI UploadFile
        destination: Destination path

    Returns:
        Path to saved file
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return destination


@router.post("/text", response_model=NormalizedResponse)
async def upload_text(request: TextUploadRequest):
    """Upload pasted text

    Returns normalized text ready for agent processing
    """
    try:
        normalized = normalize_text(request.text, source_label=request.label)
        return NormalizedResponse(**normalized.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Text processing failed: {str(e)}")


@router.post("/file", response_model=NormalizedResponse)
async def upload_file(
    file: UploadFile = File(...),
):
    """Upload a single file (PDF, DOCX, or image)

    Returns normalized content ready for agent processing
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".txt", ".md"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Save uploaded file
        upload_dir = Path(settings.FILE_STORAGE_PATH) / "uploads"
        file_path = upload_dir / file.filename
        save_upload_file(file, file_path)

        # Normalize content
        normalized = normalize_file(str(file_path))

        return NormalizedResponse(**normalized.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@router.post("/files", response_model=NormalizedResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
):
    """Upload multiple files

    All files are combined into a single normalized output
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    try:
        # Save all uploaded files
        upload_dir = Path(settings.FILE_STORAGE_PATH) / "uploads"
        saved_paths = []

        for file in files:
            if not file.filename:
                continue

            file_path = upload_dir / file.filename
            save_upload_file(file, file_path)
            saved_paths.append(str(file_path))

        if not saved_paths:
            raise HTTPException(status_code=400, detail="No valid files uploaded")

        # Normalize all files together
        normalized = normalize_multiple_files(saved_paths)

        return NormalizedResponse(**normalized.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@router.get("/test")
async def test_upload():
    """Test endpoint to verify upload routes are working"""
    return {
        "status": "ok",
        "message": "Upload routes are functional",
        "storage_path": settings.FILE_STORAGE_PATH,
        "supported_formats": {
            "documents": ["pdf", "docx", "doc", "txt", "md"],
            "images": ["jpg", "jpeg", "png", "gif", "webp"]
        }
    }
