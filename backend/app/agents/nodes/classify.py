"""Classify node - sorts extracted items into goals, features, and unknowns

Categorizes raw extracted data into structured buckets.
"""

from typing import List
from pydantic import BaseModel, Field

from app.core.claude_client import get_claude_client


class ClassifiedData(BaseModel):
    """Classified requirements data"""
    client_goals: List[str] = Field(description="High-level client goals and objectives")
    features: List[str] = Field(description="Concrete features and functionality")
    unknown_requirements: List[str] = Field(description="Unclear, ambiguous, or missing requirements")


def classify_node(state: dict) -> dict:
    """Classify extracted items into goals, features, and unknowns

    Args:
        state: Current graph state with raw extracted data

    Returns:
        Updated state with classified data
    """
    client = get_claude_client()

    raw_goals = state.get("raw_goals", [])
    raw_features = state.get("raw_features", [])
    raw_requirements = state.get("raw_requirements", [])

    prompt = f"""Classify these extracted items into three categories:

RAW GOALS:
{chr(10).join(f'- {g}' for g in raw_goals)}

RAW FEATURES:
{chr(10).join(f'- {f}' for f in raw_features)}

RAW REQUIREMENTS:
{chr(10).join(f'- {r}' for r in raw_requirements)}

Classify into:
1. CLIENT_GOALS: High-level business objectives (e.g., "increase user engagement", "reduce costs")
2. FEATURES: Concrete functionality (e.g., "user authentication", "payment processing")
3. UNKNOWN_REQUIREMENTS: Anything unclear, ambiguous, contradictory, or missing critical details

If something is mentioned but vague or incomplete, put it in UNKNOWN_REQUIREMENTS."""

    system_prompt = """You are a requirements analyst. Distinguish between high-level goals (WHY),
concrete features (WHAT), and unclear items that need clarification."""

    classified = client.structured_output(
        prompt=prompt,
        schema=ClassifiedData,
        system_prompt=system_prompt
    )

    return {
        "client_goals": classified.client_goals,
        "features": classified.features,
        "unknown_requirements": classified.unknown_requirements,
    }
