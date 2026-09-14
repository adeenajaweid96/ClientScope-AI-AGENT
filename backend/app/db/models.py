"""SQLAlchemy database models

Defines tables for projects, input files, and spec versions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Project(Base):
    """Project metadata"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, archived, deleted

    # Relationships
    input_files = relationship("InputFile", back_populates="project", cascade="all, delete-orphan")
    spec_versions = relationship("SpecVersion", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class InputFile(Base):
    """Uploaded input files associated with a project"""
    __tablename__ = "input_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # pdf, docx, image, text, mixed
    storage_path = Column(String(500), nullable=True)  # file path if uploaded
    extracted_text = Column(Text, nullable=False)  # normalized text content
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    project = relationship("Project", back_populates="input_files")

    def __repr__(self):
        return f"<InputFile(id={self.id}, project_id={self.project_id}, source_type='{self.source_type}')>"


class SpecVersion(Base):
    """Project specification versions (tracks all iterations)"""
    __tablename__ = "spec_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)  # 1, 2, 3, ...
    state_json = Column(JSON, nullable=False)  # Full ProjectSpecState as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Quick-access fields (denormalized from state_json for queries)
    complexity_score = Column(Float, nullable=True)
    risk_count = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)

    # Relationship
    project = relationship("Project", back_populates="spec_versions")

    def __repr__(self):
        return f"<SpecVersion(id={self.id}, project_id={self.project_id}, version={self.version_number})>"
