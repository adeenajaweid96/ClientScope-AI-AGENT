"""Questions node - generates follow-up questions from unknowns

Converts unknown requirements into concrete questions to ask the client.
"""

from typing import List
from pydantic import BaseModel, Field

from app.core.claude_client import get_claude_client


class FollowUpQuestions(BaseModel):
    """Generated follow-up questions"""
    follow_up_questions: List[str] = Field(description="Concrete questions to ask the client")


def questions_node(state: dict) -> dict:
    """Generate follow-up questions from unknown requirements

    Args:
        state: Current graph state with unknown requirements and risks

    Returns:
        Updated state with follow-up questions
    """
    client = get_claude_client()

    project_name = state.get("project_name", "Unknown Project")
    unknown_requirements = state.get("unknown_requirements", [])
    risks = state.get("risks", [])

    # Filter high and medium severity risks for questions
    high_medium_risks = [r for r in risks if r.get("severity", "").lower() in ["high", "medium"]]

    prompt = f"""Generate concrete follow-up questions for this project:

PROJECT: {project_name}

UNKNOWN/UNCLEAR REQUIREMENTS:
{chr(10).join(f'- {u}' for u in unknown_requirements)}

HIGH/MEDIUM RISKS:
{chr(10).join(f'- {r.get("description", "")}' for r in high_medium_risks)}

For each unknown or risk, generate a specific, actionable question that will:
1. Clarify the requirement
2. Reduce ambiguity
3. Help estimate scope and complexity

Make questions:
- Concrete and specific (not "What are your goals?")
- Easy to answer (yes/no or short answer preferred)
- Focused on one thing per question
- Ordered by importance (critical unknowns first)

Example good questions:
- "How many concurrent users should the system support?"
- "Will users log in with email/password, or social auth (Google/Facebook)?"
- "What payment providers do you want to integrate? (Stripe, PayPal, both?)"

Avoid vague questions like "Tell me more about X" or "What do you think about Y"."""

    system_prompt = """You are a requirements analyst. Ask precise, actionable questions that
will resolve ambiguity and help scope the project accurately."""

    result = client.structured_output(
        prompt=prompt,
        schema=FollowUpQuestions,
        system_prompt=system_prompt
    )

    return {
        "follow_up_questions": result.follow_up_questions,
    }
