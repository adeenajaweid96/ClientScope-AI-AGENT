"""Extract node - pulls raw goals, features, and requirements from input

Uses Claude structured output to extract structured data.
"""

from typing import TypedDict, List
from pydantic import BaseModel, Field

from app.core.claude_client import get_claude_client
from app.agents.state import ProjectSpecState


class ExtractedData(BaseModel):
    """Raw extracted data from input text"""
    project_name: str = Field(description="Inferred project name or title")
    raw_goals: List[str] = Field(description="Client goals and objectives mentioned")
    raw_features: List[str] = Field(description="Specific features or functionality requested")
    raw_requirements: List[str] = Field(description="Technical requirements, constraints, or unclear items")


def extract_node(state: dict) -> dict:
    """Extract raw goals, features, and requirements from normalized input

    Args:
        state: Current graph state with 'input_text' key

    Returns:
        Updated state with extracted data
    """
    client = get_claude_client()
    input_text = state.get("input_text", "")

    if not input_text or len(input_text.strip()) < 20:
        raise ValueError("Input text is too short or empty")

    prompt = f"""Analyze this client input and extract structured information:

{input_text}

Extract:
1. Project name (infer from context if not explicitly stated)
2. All client goals and objectives
3. All specific features or functionality mentioned
4. All technical requirements, constraints, or anything unclear

Be thorough - capture everything mentioned, even if vague or incomplete."""

    system_prompt = """You are an expert project analyst. Extract ALL relevant information from client requirements,
including vague or incomplete details. If something is mentioned but unclear, still capture it."""

    extracted = client.structured_output(
        prompt=prompt,
        schema=ExtractedData,
        system_prompt=system_prompt
    )

    # Update state with extracted data
    return {
        "project_name": extracted.project_name,
        "raw_goals": extracted.raw_goals,
        "raw_features": extracted.raw_features,
        "raw_requirements": extracted.raw_requirements,
    }
