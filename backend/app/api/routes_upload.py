"""File upload routes

Handles uploading PDFs, DOCX files, screenshots, and pasted text.
TODO: Phase 2 - Implement file upload handling and preprocessing
"""

from fastapi import APIRouter

router = APIRouter(prefix="/upload", tags=["upload"])


@router.get("/")
async def upload_placeholder():
    """Placeholder endpoint for upload routes"""
    return {"message": "Upload routes - Not implemented yet (Phase 2)"}
