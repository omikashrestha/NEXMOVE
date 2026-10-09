from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from backend.app.schemas.state import RelocationState, AgentMessage
from backend.app.agents.housing import HousingResearchAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAnalystAgent
from backend.app.agents.document import DocumentIntelligenceAgent
from backend.app.agents.schedule import ScheduleOptimizationAgent
from backend.app.agents.decision import DecisionSynthesisAgent


class AgentGraphState(TypedDict):
    state: RelocationState


def housing_node(data: AgentGraphState) -> AgentGraphState:
    state = data["state"]
    agent = HousingResearchAgent()
    proposal = agent.search(state.profile, state.active_revision_request)
    state.housing_proposal = proposal
    state.history.append(AgentMessage(
        sender="HousingResearchAgent",
        recipient="DecisionSynthesisAgent",
        message_type="PROPOSAL",
        content=f"Proposed {proposal.neighborhood} ({proposal.title}) at ₹{proposal.monthly_rent_inr:,.0f}/mo.",
        payload=proposal.model_dump()
    ))
    return {"state": state}


def logistics_node(data: AgentGraphState) -> AgentGraphState:
    state = data["state"]
    agent = LogisticsAgent()
    estimate = agent.estimate(state.profile, state.active_revision_request)
    state.logistics_estimate = estimate
    state.history.append(AgentMessage(
        sender="LogisticsAgent",
        recipient="BudgetAnalystAgent",
        message_type="PROPOSAL",
        content=f"Estimated freight of ₹{estimate.total_logistics_inr:,.0f} with {estimate.estimated_transit_days} transit days.",
        payload=estimate.model_dump()
    ))
    return {"state": state}


def budget_node(data: AgentGraphState) -> AgentGraphState:
    state = data["state"]
    if not state.housing_proposal or not state.logistics_estimate:
        return {"state": state}
    agent = BudgetAnalystAgent()
    audit = agent.audit(state.profile, state.housing_proposal, state.logistics_estimate)
    state.budget_audit = audit
    msg_type = "AUDIT_PASS" if audit.overall_financially_feasible else "AUDIT_FAIL"
    state.history.append(AgentMessage(
        sender="BudgetAnalystAgent",
        recipient="DecisionSynthesisAgent",
        message_type=msg_type,
        content=audit.summary_notes,
        payload=audit.model_dump()
    ))
    return {"state": state}


def document_node(data: AgentGraphState) -> AgentGraphState:
    state = data["state"]
    # If no document was already analyzed in state, produce standard or default audit
    if not state.document_audit:
        agent = DocumentIntelligenceAgent()
        # By default create a baseline success audit
        audit = agent.analyze_document(raw_text_content=None)
        state.document_audit = audit
    return {"state": state}


def schedule_node(data: AgentGraphState) -> AgentGraphState:
    state = data["state"]
    if not state.housing_proposal or not state.logistics_estimate:
        return {"state": state}
    agent = ScheduleOptimizationAgent()
    schedule_plan = agent.build_schedule(
        profile=state.profile,
        logistics_estimate=state.logistics_estimate,
        housing_proposal=state.housing_proposal,
        document_audit=state.document_audit
    )
    state.schedule_plan = schedule_plan
    return {"state": state}


def decision_node(data: AgentGraphState) -> AgentGraphState:
    state = data["state"]
    agent = DecisionSynthesisAgent()
    updated_state = agent.evaluate_and_arbitrate(state)
    return {"state": updated_state}


def route_decision(data: AgentGraphState) -> str:
    """Conditional routing based on Decision Agent arbitration status."""
    state = data["state"]
    if state.status == "REVISING":
        return "housing_node"
    return END


def build_relocation_graph():
    """Compiles the multi-agent LangGraph state machine with bounded revision looping."""
    workflow = StateGraph(AgentGraphState)

    workflow.add_node("housing_node", housing_node)
    workflow.add_node("logistics_node", logistics_node)
    workflow.add_node("budget_node", budget_node)
    workflow.add_node("document_node", document_node)
    workflow.add_node("schedule_node", schedule_node)
    workflow.add_node("decision_node", decision_node)

    # Core execution pipeline
    workflow.add_edge(START, "housing_node")
    workflow.add_edge("housing_node", "logistics_node")
    workflow.add_edge("logistics_node", "budget_node")
    workflow.add_edge("budget_node", "document_node")
    workflow.add_edge("document_node", "schedule_node")
    workflow.add_edge("schedule_node", "decision_node")

    # Conditional branching for bounded revision loops
    workflow.add_conditional_edges(
        "decision_node",
        route_decision,
        {
            "housing_node": "housing_node",
            END: END
        }
    )

    return workflow.compile()


def run_relocation_workflow(initial_state: RelocationState) -> RelocationState:
    """Invokes the compiled LangGraph multi-agent pipeline and returns the synthesized state."""
    if initial_state.status != "REVISING":
        initial_state.iteration_count = 1
        initial_state.active_revision_request = None
        initial_state.active_conflicts = []
        initial_state.status = "INITIALIZED"

    graph = build_relocation_graph()
    result = graph.invoke({"state": initial_state})
    return result["state"]

