from src.workflows.decision_state import LoanApplicationState

def pi_deletion_node(state: LoanApplicationState) ->  LoanApplicationState:
    """
    Final Decision Node (LLM)

    Responsibility:
    - Compare requested vs calculated limit
    - Approve / Reject / Counter-offer
    - Set next_step routing flag
    - Provide explainability reasoning

    Input:
        state["requested_amount"]
        state["requested_tenure"]
        state["aggregated_risk"]

    Output:
        state["decision_result"]
        state["next_step"]
    """

    return state