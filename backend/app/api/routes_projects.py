"""Project management routes

Handles project CRUD operations, spec retrieval, and feedback loop.
Endpoints: POST /projects, GET /projects/{id}, POST /projects/{id}/answer, GET /projects/{id}/export
TODO: Phase 4 - Implement project persistence and retrieval
TODO: Phase 5 - Implement feedback loop endpoint
"""

from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
async def projects_placeholder():
    """Placeholder endpoint for project routes"""
    return {"message": "Project routes - Not implemented yet (Phase 4)"}
