from langgraph.graph import StateGraph, END
from app.agent.state import InterviewState
from app.agent.graphs.base import (
    INTERVIEW_FLOWS,
    generate_response,
    evaluate_and_route,
    normalize_interview_type,
)


def build_graph(interview_type: str = "general"):
    """
    Builds the LangGraph state graph for the interview agent.
    """
    workflow = StateGraph(InterviewState)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("evaluate_and_route", evaluate_and_route)

    workflow.set_entry_point("generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


__all__ = [
    "build_graph",
    "evaluate_and_route",
    "generate_response",
    "INTERVIEW_FLOWS",
    "normalize_interview_type",
]
