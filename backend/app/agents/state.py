"""Pydantic models for LangGraph state

TODO: Phase 3 - Implement ProjectSpecState and Risk models
TODO: Phase 3 - Define state schema for the agent pipeline
"""

from pydantic import BaseModel
from typing import Literal


class Risk(BaseModel):
    """Risk assessment for a project requirement"""
    description: str
    severity: Literal["low", "medium", "high"]


class ProjectSpecState(BaseModel):
    """Shared state object passed through the LangGraph pipeline"""
    project_name: str = ""
    client_goals: list[str] = []
    features: list[str] = []
    unknown_requirements: list[str] = []
    risks: list[Risk] = []
    complexity_score: float = 0.0  # 0-10
    follow_up_questions: list[str] = []
