"""LangGraph pipeline orchestration

Wires all 7 nodes into a sequential processing pipeline:
1. Extract → 2. Classify → 3. Risk → 4. Complexity → 5. Questions
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.state import ProjectSpecState
from app.agents.nodes.extract import extract_node
from app.agents.nodes.classify import classify_node
from app.agents.nodes.risk import risk_node
from app.agents.nodes.complexity import complexity_node
from app.agents.nodes.questions import questions_node


class GraphState(TypedDict, total=False):
    """State dict for LangGraph - uses TypedDict for type hints"""
    # Input
    input_text: str

    # Extracted data
    project_name: str
    raw_goals: List[str]
    raw_features: List[str]
    raw_requirements: List[str]

    # Classified data
    client_goals: List[str]
    features: List[str]
    unknown_requirements: List[str]

    # Risk assessment
    risks: List[dict]

    # Complexity score
    complexity_score: float
    complexity_reasoning: str

    # Follow-up questions
    follow_up_questions: List[str]


def create_spec_graph() -> StateGraph:
    """Create the project specification extraction graph

    Pipeline: Extract → Classify → Risk → Complexity → Questions

    Returns:
        Compiled LangGraph StateGraph
    """
    # Create state graph with TypedDict state
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("extract", extract_node)
    graph.add_node("classify", classify_node)
    graph.add_node("risk", risk_node)
    graph.add_node("complexity", complexity_node)
    graph.add_node("questions", questions_node)

    # Define edges (linear pipeline)
    graph.set_entry_point("extract")
    graph.add_edge("extract", "classify")
    graph.add_edge("classify", "risk")
    graph.add_edge("risk", "complexity")
    graph.add_edge("complexity", "questions")
    graph.add_edge("questions", END)

    # Compile graph
    return graph.compile()


# Global graph instance
_graph = None


def get_spec_graph():
    """Get or create the compiled graph instance"""
    global _graph
    if _graph is None:
        _graph = create_spec_graph()
    return _graph


async def run_spec_pipeline(input_text: str) -> ProjectSpecState:
    """Run the full specification extraction pipeline

    Args:
        input_text: Raw client input (from normalizer)

    Returns:
        Complete ProjectSpecState with all fields populated

    Raises:
        ValueError: If input is invalid or pipeline fails
    """
    if not input_text or len(input_text.strip()) < 20:
        raise ValueError("Input text must be at least 20 characters")

    graph = get_spec_graph()

    # Initialize state as dict
    initial_state: GraphState = {
        "input_text": input_text,
        "project_name": "",
        "raw_goals": [],
        "raw_features": [],
        "raw_requirements": [],
        "client_goals": [],
        "features": [],
        "unknown_requirements": [],
        "risks": [],
        "complexity_score": 0.0,
        "complexity_reasoning": "",
        "follow_up_questions": [],
    }

    # Run graph
    result = await graph.ainvoke(initial_state)

    # Convert result dict to Pydantic model
    return ProjectSpecState.model_validate(result)


def run_spec_pipeline_sync(input_text: str) -> ProjectSpecState:
    """Synchronous version of run_spec_pipeline

    Args:
        input_text: Raw client input (from normalizer)

    Returns:
        Complete ProjectSpecState with all fields populated
    """
    if not input_text or len(input_text.strip()) < 20:
        raise ValueError("Input text must be at least 20 characters")

    graph = get_spec_graph()

    # Initialize state as dict
    initial_state: GraphState = {
        "input_text": input_text,
        "project_name": "",
        "raw_goals": [],
        "raw_features": [],
        "raw_requirements": [],
        "client_goals": [],
        "features": [],
        "unknown_requirements": [],
        "risks": [],
        "complexity_score": 0.0,
        "complexity_reasoning": "",
        "follow_up_questions": [],
    }

    # Run graph synchronously
    result = graph.invoke(initial_state)

    # Convert result dict to Pydantic model
    return ProjectSpecState.model_validate(result)
