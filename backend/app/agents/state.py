"""Pydantic models for LangGraph state

Defines the shared state object passed through the agent pipeline.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Risk(BaseModel):
    """Risk assessment for a project requirement"""
    description: str = Field(description="What the risk is")
    severity: Literal["low", "medium", "high"] = Field(description="Risk severity level")


class ProjectSpecState(BaseModel):
    """Shared state object passed through the LangGraph pipeline

    This is both the internal state and the final API response format.
    """
    # Input
    input_text: str = Field(default="", description="Raw input text to process")

    # Extracted data (from extract node)
    project_name: str = Field(default="", description="Project name or title")
    raw_goals: List[str] = Field(default_factory=list, description="Raw extracted goals")
    raw_features: List[str] = Field(default_factory=list, description="Raw extracted features")
    raw_requirements: List[str] = Field(default_factory=list, description="Raw extracted requirements")

    # Classified data (from classify node)
    client_goals: List[str] = Field(default_factory=list, description="High-level client goals")
    features: List[str] = Field(default_factory=list, description="Specific features requested")
    unknown_requirements: List[str] = Field(default_factory=list, description="Unclear or missing requirements")

    # Risk assessment (from risk node)
    risks: List[dict] = Field(default_factory=list, description="Identified risks with severity")

    # Complexity score (from complexity node)
    complexity_score: float = Field(default=0.0, description="Complexity score 0-10")
    complexity_reasoning: str = Field(default="", description="Reasoning for complexity score")

    # Follow-up questions (from questions node)
    follow_up_questions: List[str] = Field(default_factory=list, description="Questions to ask the client")

    class Config:
        # Allow mutation for LangGraph state updates
        frozen = False
