"""Risk node - flags ambiguous/missing/contradictory requirements

Assesses risks and assigns severity levels.
"""

from typing import List
from pydantic import BaseModel, Field
from typing import Literal

from app.core.claude_client import get_claude_client
from app.agents.state import Risk


class RiskAssessment(BaseModel):
    """Risk assessment results"""
    risks: List[Risk] = Field(description="Identified risks with severity levels")


def risk_node(state: dict) -> dict:
    """Assess risks from unknown requirements and potential issues

    Args:
        state: Current graph state with classified data

    Returns:
        Updated state with risk assessment
    """
    client = get_claude_client()

    project_name = state.get("project_name", "Unknown Project")
    features = state.get("features", [])
    unknown_requirements = state.get("unknown_requirements", [])

    prompt = f"""Assess risks for this project:

PROJECT: {project_name}

FEATURES:
{chr(10).join(f'- {f}' for f in features)}

UNKNOWN/UNCLEAR REQUIREMENTS:
{chr(10).join(f'- {u}' for u in unknown_requirements)}

Identify risks including:
- Missing critical information (auth requirements, data storage, scale)
- Ambiguous or contradictory requirements
- Technical feasibility concerns
- Timeline/budget mismatches
- Security or compliance gaps

For each risk, assign severity:
- HIGH: Project-blocking, must be resolved before starting
- MEDIUM: Significant impact, should be clarified early
- LOW: Minor uncertainty, can be resolved during development"""

    system_prompt = """You are a technical project risk analyst. Flag everything that could cause
problems: missing details, unrealistic expectations, unclear requirements, or contradictions."""

    assessment = client.structured_output(
        prompt=prompt,
        schema=RiskAssessment,
        system_prompt=system_prompt
    )

    return {
        "risks": [risk.model_dump() for risk in assessment.risks],
    }
