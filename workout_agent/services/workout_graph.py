"""LangGraph orchestration graph for the 8-agent workout pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from workout_agent.agents import (
    constraint_receiver,
    exercise_selector,
    explainability,
    information_receiver,
    plan_export,
    progress_planner,
    risk_assessment,
    schedule_maker,
)
from workout_agent.core.state import AgentState


def _route_after_risk(state: AgentState) -> str:
    return "exercise_selector" if state["should_reselect_exercises"] else "explainability"


def build_workout_graph():
    """Build and compile the multi-agent workout generation graph."""

    graph = StateGraph(AgentState)

    graph.add_node("information_receiver", information_receiver.run)
    graph.add_node("constraint_receiver", constraint_receiver.run)
    graph.add_node("exercise_selector", exercise_selector.run)
    graph.add_node("schedule_maker", schedule_maker.run)
    graph.add_node("progress_planner", progress_planner.run)
    graph.add_node("risk_assessment", risk_assessment.run)
    graph.add_node("explainability", explainability.run)
    graph.add_node("plan_export", plan_export.run)

    graph.set_entry_point("information_receiver")
    graph.add_edge("information_receiver", "constraint_receiver")
    graph.add_edge("constraint_receiver", "exercise_selector")
    graph.add_edge("exercise_selector", "schedule_maker")
    graph.add_edge("schedule_maker", "progress_planner")
    graph.add_edge("progress_planner", "risk_assessment")

    graph.add_conditional_edges(
        "risk_assessment",
        _route_after_risk,
        {
            "exercise_selector": "exercise_selector",
            "explainability": "explainability",
        },
    )

    graph.add_edge("explainability", "plan_export")
    graph.add_edge("plan_export", END)

    return graph.compile()
