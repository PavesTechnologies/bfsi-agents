"""
Income & Affordability Engine
DTI & EMI Capacity Evaluator
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.services.rules_db import MissingRuleError
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.income_model.income_parser import IncomeOutput
from src.services.income_model.income_prompt import INCOME_PROMPT


@track_node("income_engine")
@audit_node(agent_name="decisioning_agent")
def income_node(state: LoanApplicationState) -> LoanApplicationState:
    active = state.get("active_analyzers")
    if active is not None and "income" not in active:
        return {}

    income_output_parser = PydanticOutputParser(
        pydantic_object=IncomeOutput
    )

    # ==================================================
    # 1️⃣ Extract Data Sources
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    # Income may come from bank statement summary or employment info
    bank_statement = state.get("bank_statement_summary", {})

    monthly_income = None
    if bank_statement:
        monthly_income = bank_statement.get("monthly_income")

    # Monthly obligations from employment or estimated from tradelines
    tradelines = raw_experian.get("tradeline", [])
    open_trades = [t for t in tradelines if t.get("openOrClosed") == "O"]

    # Calculate total monthly obligations from open tradelines
    total_monthly = 0
    for trade in open_trades:
        payment = trade.get("monthlyPaymentAmount")
        if payment:
            total_monthly += int(payment)

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "monthly_income": str(monthly_income) if monthly_income else "UNKNOWN",
        "monthly_obligations": str(total_monthly),
        "rbi_context": state.get("rbi_common_context", ""),
        "policy_context": state.get("rag_context_per_node", {}).get("income_analysis", ""),
        "format_instructions": income_output_parser.get_format_instructions(),
    }

    # print(inputs)

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=INCOME_PROMPT,
        inputs=inputs,
        parser=income_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    income_data = result.model_dump()

    # ==================================================
    # 5️⃣ Deterministic override — affordability_flag
    # ==================================================
    # The LLM frequently miscompares floats here ("DTI 0.467 > 0.50" etc.),
    # which then misleads the decision node's Step 1c hard-decline check.
    # Compute the flag in Python from DTI so it's always correct.
    income_rules = (state.get("rules_per_node") or {}).get("income_analysis") or {}
    threshold_raw = income_rules.get("max_dti_threshold")
    if threshold_raw is None:
        raise MissingRuleError(rule_key="max_dti_threshold", category="dti")
    threshold = float(threshold_raw)
    if income_data.get("income_missing_flag"):
        income_data["affordability_flag"] = False
    else:
        try:
            dti_val = float(income_data.get("estimated_dti"))
            income_data["affordability_flag"] = dti_val <= threshold
        except (TypeError, ValueError):
            # Fall back to whatever the LLM said if DTI isn't numeric.
            pass

    income_data["affordability_threshold_applied"] = threshold

    income_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"income_data": income_data}