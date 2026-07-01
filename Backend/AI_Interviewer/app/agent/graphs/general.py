from langgraph.graph import StateGraph, END
from app.agent.state import InterviewStage, InterviewState
from app.agent.graphs.base import generate_response, evaluate_and_route

def build_general_graph():
    workflow = StateGraph(InterviewState)

    workflow.add_node("generate_response", generate_response)
    workflow.add_node("evaluate_and_route", evaluate_and_route)

    # Entry point is always generating a response based on current stage
    workflow.set_entry_point("generate_response")
    workflow.add_edge("generate_response", "evaluate_and_route")
    workflow.add_edge("evaluate_and_route", END)

    return workflow.compile()
