"""
Income & Affordability Engine
DTI & EMI Capacity Evaluator
"""

from datetime import datetime

from src.core.telemetry import track_node
from src.domain.calculators.dti import (
    affordability_from_dti,
    calculate_dti,
    classify_dti_risk,
)
from src.services.income_model.income_parser import IncomeOutput
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


@track_node("income_engine")
@audit_node(agent_name="decisioning_agent")
def income_node(state: LoanApplicationState) -> LoanApplicationState:
    raw_experian = state.get("pi_masked_experian_data")
    bank_statement = state.get("bank_statement_summary", {})

    monthly_income = None
    if bank_statement:
        monthly_income = bank_statement.get("monthly_income")

    tradelines = raw_experian.get("tradeline", [])
    open_trades = [t for t in tradelines if t.get("openOrClosed") == "O"]

    total_monthly = 0
    for trade in open_trades:
        payment = trade.get("monthlyPaymentAmount")
        if payment:
            total_monthly += int(payment)

    income_missing = monthly_income in (None, 0, "UNKNOWN")
    estimated_dti = calculate_dti(monthly_income, total_monthly)
    income_risk = classify_dti_risk(estimated_dti, income_missing)
    affordability_flag = affordability_from_dti(estimated_dti, income_missing)

    result = IncomeOutput(
        estimated_dti=estimated_dti,
        income_risk=income_risk,
        affordability_flag=affordability_flag,
        income_missing_flag=income_missing,
        confidence_score=1.0 if not income_missing else 0.5,
        model_reasoning=(
            "Income missing; affordability failed deterministically."
            if income_missing
            else (
                f"Calculated DTI as {estimated_dti:.4f} from monthly obligations "
                f"{total_monthly} and monthly income {float(monthly_income):.2f}."
            )
        ),
    )

    income_data = result.model_dump()
    income_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"income_data": income_data}
