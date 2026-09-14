"""Complexity node - calculates 0-10 complexity score

Combines feature count, risk severity, and technical requirements.
"""

from pydantic import BaseModel, Field

from app.core.claude_client import get_claude_client


class ComplexityScore(BaseModel):
    """Project complexity assessment"""
    complexity_score: float = Field(description="Complexity score from 0-10", ge=0, le=10)
    reasoning: str = Field(description="Explanation of the score")


def complexity_node(state: dict) -> dict:
    """Calculate project complexity score (0-10)

    Args:
        state: Current graph state with features and risks

    Returns:
        Updated state with complexity score
    """
    client = get_claude_client()

    project_name = state.get("project_name", "Unknown Project")
    features = state.get("features", [])
    risks = state.get("risks", [])
    unknown_requirements = state.get("unknown_requirements", [])

    # Count high/medium/low risks
    risk_counts = {"high": 0, "medium": 0, "low": 0}
    for risk in risks:
        severity = risk.get("severity", "low").lower()
        risk_counts[severity] = risk_counts.get(severity, 0) + 1

    prompt = f"""Calculate a complexity score (0-10) for this project:

PROJECT: {project_name}

FEATURES ({len(features)} total):
{chr(10).join(f'- {f}' for f in features[:10])}
{'...' if len(features) > 10 else ''}

RISKS:
- High severity: {risk_counts['high']}
- Medium severity: {risk_counts['medium']}
- Low severity: {risk_counts['low']}

UNKNOWN REQUIREMENTS: {len(unknown_requirements)}

Score based on:
- Number and complexity of features (more features = higher score)
- Number and severity of risks (more/severe risks = higher score)
- Number of unknowns (more unknowns = higher uncertainty = higher score)

Scale:
0-2: Simple project, few features, minimal risk
3-4: Basic project, standard features, some unknowns
5-6: Moderate complexity, multiple features, several risks
7-8: Complex project, many features, significant risks
9-10: Very complex, extensive features, high risk/uncertainty"""

    system_prompt = """You are a technical project estimator. Score complexity objectively
based on feature count, risk severity, and uncertainty."""

    result = client.structured_output(
        prompt=prompt,
        schema=ComplexityScore,
        system_prompt=system_prompt
    )

    return {
        "complexity_score": result.complexity_score,
        "complexity_reasoning": result.reasoning,
    }
