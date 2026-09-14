"""Project management routes

Handles project CRUD operations, spec retrieval, and feedback loop.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.agents.graph import run_spec_pipeline_sync
from app.agents.state import ProjectSpecState
from app.db.session import get_db
from app.db.models import Project, SpecVersion, InputFile

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    """Request to create a new project from text input"""
    text: str
    label: Optional[str] = "client_input"


class AnswerFeedbackRequest(BaseModel):
    """Request to answer a follow-up question"""
    question: str
    answer: str


class ProjectResponse(BaseModel):
    """Project metadata response"""
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    status: str
    latest_version: int


class SpecVersionResponse(BaseModel):
    """Spec version response"""
    version_number: int
    created_at: datetime
    project_name: str
    client_goals: List[str]
    features: List[str]
    unknown_requirements: List[str]
    risks: List[dict]
    complexity_score: float
    follow_up_questions: List[str]


@router.post("/", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest, db: Session = Depends(get_db)):
    """Create a new project and generate initial specification

    Runs the full agent pipeline and persists:
    - Project metadata
    - Input file record
    - Initial spec version (v1)
    """
    try:
        # Validate input
        if not request.text or len(request.text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Input text must be at least 20 characters"
            )

        # Run agent pipeline
        spec = run_spec_pipeline_sync(request.text)

        # Create project
        project = Project(
            name=spec.project_name or "Untitled Project",
            status="active"
        )
        db.add(project)
        db.flush()  # Get project.id before committing

        # Create input file record
        input_file = InputFile(
            project_id=project.id,
            source_type="text",
            storage_path=None,
            extracted_text=request.text
        )
        db.add(input_file)

        # Create initial spec version
        spec_version = SpecVersion(
            project_id=project.id,
            version_number=1,
            state_json=spec.model_dump(),
            complexity_score=spec.complexity_score,
            risk_count=len(spec.risks),
            feature_count=len(spec.features)
        )
        db.add(spec_version)

        # Commit transaction
        db.commit()
        db.refresh(project)

        return ProjectResponse(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
            status=project.status,
            latest_version=1
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.post("/{project_id}/answer", response_model=SpecVersionResponse)
async def answer_feedback_question(
    project_id: int,
    request: AnswerFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Answer a follow-up question and update specification

    Phase 5: Feedback loop implementation
    - Takes the original input + new Q&A
    - Re-runs the pipeline with enriched context
    - Creates a new spec version
    - Unknown requirements should decrease as questions are answered
    """
    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all input files for context
        input_files = db.query(InputFile).filter(
            InputFile.project_id == project_id
        ).order_by(InputFile.created_at.asc()).all()

        if not input_files:
            raise HTTPException(status_code=404, detail="No input found for project")

        # Get latest spec version to understand current state
        latest_version = db.query(SpecVersion).filter(
            SpecVersion.project_id == project_id
        ).order_by(SpecVersion.version_number.desc()).first()

        if not latest_version:
            raise HTTPException(status_code=404, detail="No spec version found")

        # Build enriched input - clearer format for agent pipeline
        original_text = input_files[0].extracted_text  # Use only the original requirements

        # Add Q&A as additional requirements/clarifications
        enriched_input = f"""{original_text}

ADDITIONAL CLARIFICATION PROVIDED:

Q: {request.question}
A: {request.answer}

[Note: The above answer provides additional detail that clarifies the project requirements.
Update the specification accordingly, resolving related unknowns and refining features/goals.]"""

        # Create new input file record for the Q&A
        qa_input = InputFile(
            project_id=project_id,
            source_type="text",
            storage_path=None,
            extracted_text=f"Q: {request.question}\nA: {request.answer}"
        )
        db.add(qa_input)

        # Re-run agent pipeline with enriched context
        updated_spec = run_spec_pipeline_sync(enriched_input)

        # Create new spec version
        new_version_number = latest_version.version_number + 1
        new_spec_version = SpecVersion(
            project_id=project_id,
            version_number=new_version_number,
            state_json=updated_spec.model_dump(),
            complexity_score=updated_spec.complexity_score,
            risk_count=len(updated_spec.risks),
            feature_count=len(updated_spec.features)
        )
        db.add(new_spec_version)

        # Update project timestamp
        project.updated_at = datetime.utcnow()

        # Commit transaction
        db.commit()
        db.refresh(new_spec_version)

        return SpecVersionResponse(
            version_number=new_spec_version.version_number,
            created_at=new_spec_version.created_at,
            project_name=updated_spec.project_name,
            client_goals=updated_spec.client_goals,
            features=updated_spec.features,
            unknown_requirements=updated_spec.unknown_requirements,
            risks=updated_spec.risks,
            complexity_score=updated_spec.complexity_score,
            follow_up_questions=updated_spec.follow_up_questions
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update spec: {str(e)}")


@router.get("/{project_id}", response_model=SpecVersionResponse)
async def get_project(project_id: int, version: Optional[int] = None, db: Session = Depends(get_db)):
    """Get project specification

    Returns the latest version by default, or a specific version if specified.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get spec version
    if version:
        spec_version = db.query(SpecVersion).filter(
            SpecVersion.project_id == project_id,
            SpecVersion.version_number == version
        ).first()
    else:
        spec_version = db.query(SpecVersion).filter(
            SpecVersion.project_id == project_id
        ).order_by(SpecVersion.version_number.desc()).first()

    if not spec_version:
        raise HTTPException(status_code=404, detail="Spec version not found")

    # Extract data from JSON
    state = spec_version.state_json

    return SpecVersionResponse(
        version_number=spec_version.version_number,
        created_at=spec_version.created_at,
        project_name=state.get("project_name", ""),
        client_goals=state.get("client_goals", []),
        features=state.get("features", []),
        unknown_requirements=state.get("unknown_requirements", []),
        risks=state.get("risks", []),
        complexity_score=state.get("complexity_score", 0.0),
        follow_up_questions=state.get("follow_up_questions", [])
    )


@router.get("/{project_id}/versions", response_model=List[dict])
async def get_project_versions(project_id: int, db: Session = Depends(get_db)):
    """Get all spec versions for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all versions
    versions = db.query(SpecVersion).filter(
        SpecVersion.project_id == project_id
    ).order_by(SpecVersion.version_number.asc()).all()

    return [
        {
            "version_number": v.version_number,
            "created_at": v.created_at,
            "complexity_score": v.complexity_score,
            "risk_count": v.risk_count,
            "feature_count": v.feature_count
        }
        for v in versions
    ]


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    projects = db.query(Project).filter(Project.status == "active").order_by(Project.created_at.desc()).all()

    result = []
    for project in projects:
        # Get latest version number
        latest_version = db.query(SpecVersion).filter(
            SpecVersion.project_id == project.id
        ).order_by(SpecVersion.version_number.desc()).first()

        result.append(ProjectResponse(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
            status=project.status,
            latest_version=latest_version.version_number if latest_version else 0
        ))

    return result


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project (soft delete - sets status to 'deleted')"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "deleted"
    db.commit()

    return {"message": "Project deleted successfully", "project_id": project_id}
