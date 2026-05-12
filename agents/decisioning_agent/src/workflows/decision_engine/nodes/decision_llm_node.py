"""
Underwriting Decision Engine.

All numeric / decision logic is computed deterministically in Python and
injected into the prompt as pre-computed values. The LLM's only job is to
write the human-readable explanation and reasoning_steps. After the LLM
returns, every numeric / decision field is overwritten with Python's
authoritative values, so the response cannot drift.
"""

import json
from datetime import datetime
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.services.decision_model.decision_parser import DecisionOutput
from src.services.decision_model.decision_prompt import DECISION_PROMPT
from src.services.llm_executor import execute_llm
from src.services.rules_db import MissingRuleError
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


def _decision_rules(state: LoanApplicationState) -> dict[str, Any]:
    rules = (state.get("rules_per_node") or {}).get("decision")
    if not rules:
        raise MissingRuleError(rule_key="<decision-bucket>", category="decision")
    return rules


def _interest_rate_for_tier(tier: str, rates: dict[str, float]) -> float:
    # JSON deserializes keys as strings — ensure tier lookup matches.
    return float(rates.get(str(tier), 0.0))


# Canonical analyzer order — drives the "ran vs skipped" lists fed to the
# LLM. Mandatory analyzers (credit_score, public_record, income) always run,
# so they always render real JSON for their *_data prompt slots.
_ALL_ANALYZERS: list[str] = [
    "credit_score",
    "public_record",
    "utilization",
    "exposure",
    "behavior",
    "inquiry",
    "income",
]


def _split_active(state: LoanApplicationState) -> tuple[list[str], list[str]]:
    """Return (analyzers_that_ran, analyzers_that_were_skipped) in canonical order."""
    active = state.get("active_analyzers")
    if active is None:
        return list(_ALL_ANALYZERS), []
    ran = [a for a in _ALL_ANALYZERS if a in active]
    skipped = [a for a in _ALL_ANALYZERS if a not in active]
    return ran, skipped


def _data_for_prompt(
    state: LoanApplicationState, state_key: str, analyzer_id: str
) -> str:
    """Render an analyzer's data slot for the prompt. Skipped analyzers get a
    literal sentinel string so the LLM cannot hallucinate the missing fields."""
    active = state.get("active_analyzers")
    if active is not None and analyzer_id not in active:
        return "(skipped — analyzer not selected by bank)"
    return json.dumps(state.get(state_key) or {})


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic computation helpers
# ─────────────────────────────────────────────────────────────────────────────


def _compute_max_approved_amount(state: LoanApplicationState) -> float:
    """
    max_approved_amount = base_limit_band
                          × public_record_adjustment_factor
                          × utilization_adjustment_factor
                          × inquiry_penalty_factor
    """
    credit = state.get("credit_score_data") or {}
    public = state.get("public_record_data") or {}
    util = state.get("utilization_data") or {}
    inquiry = state.get("inquiry_data") or {}

    base_limit = float(credit.get("base_limit_band") or 0)
    pr_factor = float(public.get("public_record_adjustment_factor") or 1.0)
    util_factor = float(util.get("utilization_adjustment_factor") or 1.0)
    inq_factor = float(inquiry.get("inquiry_penalty_factor") or 1.0)

    return round(base_limit * pr_factor * util_factor * inq_factor, 2)


def _step1_hard_decline_triggers(state: LoanApplicationState) -> list[str]:
    """Return the list of Step 1 triggers that fired (empty list if none)."""
    triggers: list[str] = []

    if state.get("aggregated_risk_tier") == "F":
        triggers.append("aggregated_risk_tier == 'F'")

    public_record = state.get("public_record_data") or {}
    if public_record.get("hard_decline_flag") is True:
        triggers.append("public_record.hard_decline_flag == True")

    income = state.get("income_data") or {}
    if income.get("affordability_flag") is False:
        triggers.append("income.affordability_flag == False")

    return triggers


def _compute_decision(
    state: LoanApplicationState,
    requested_amount: float,
    requested_tenure: int,
    max_approved_amount: float,
) -> dict:
    """
    Decide everything numeric in Python. Returns a dict with:
      decision, approved_amount, approved_tenure, interest_rate,
      disbursement_amount, max_approved_amount, step1_triggers, routing_rule.
    """
    decision_rules = _decision_rules(state)
    tier_interest_rates: dict[str, float] = decision_rules["tier_interest_rates"]
    fee_pct = float(decision_rules["origination_fee_pct"])

    triggers = _step1_hard_decline_triggers(state)
    tier = state.get("aggregated_risk_tier") or "F"

    if triggers:
        return {
            "decision": "DECLINE",
            "approved_amount": 0.0,
            "approved_tenure": 0,
            "interest_rate": 0.0,
            "disbursement_amount": 0.0,
            "max_approved_amount": max_approved_amount,
            "step1_triggers": triggers,
            "routing_rule": "DECLINE — Step 1 hard-decline trigger(s) fired",
        }

    interest_rate = _interest_rate_for_tier(tier, tier_interest_rates)

    if requested_amount <= max_approved_amount:
        return {
            "decision": "APPROVE",
            "approved_amount": requested_amount,
            "approved_tenure": requested_tenure,
            "interest_rate": interest_rate,
            "disbursement_amount": round(requested_amount * (1 - fee_pct), 2),
            "max_approved_amount": max_approved_amount,
            "step1_triggers": [],
            "routing_rule": (
                f"RULE A: requested ({requested_amount:.2f}) <= "
                f"max ({max_approved_amount:.2f}) → APPROVE"
            ),
        }

    # requested > max → counter-offer
    return {
        "decision": "COUNTER_OFFER",
        "approved_amount": 0.0,
        "approved_tenure": 0,
        "interest_rate": interest_rate,
        "disbursement_amount": 0.0,
        "max_approved_amount": max_approved_amount,
        "step1_triggers": [],
        "routing_rule": (
            f"RULE B: requested ({requested_amount:.2f}) > "
            f"max ({max_approved_amount:.2f}) → COUNTER_OFFER"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Fallback (used when the LLM call completely fails — same numbers, generic text)
# ─────────────────────────────────────────────────────────────────────────────


def _build_fallback_decision_result(pre: dict) -> DecisionOutput:
    decision = pre["decision"]
    triggers = pre["step1_triggers"]
    routing_rule = pre["routing_rule"]

    if decision == "DECLINE":
        explanation = (
            "Application declined. Hard-decline trigger fired: "
            + ", ".join(triggers)
            + "."
        )
        reasoning = ["DETERMINISTIC DECLINE — LLM explanation unavailable."] + triggers
    elif decision == "APPROVE":
        explanation = (
            "Application approved per deterministic underwriting policy. "
            "Requested amount is within the borrower's qualifying cap."
        )
        reasoning = [
            "All Step 1 hard-decline checks passed.",
            routing_rule,
            f"Interest rate {pre['interest_rate']}% applied.",
        ]
    else:  # COUNTER_OFFER
        explanation = (
            "Counter-offer issued — requested amount exceeds the borrower's "
            f"qualifying cap of {pre['max_approved_amount']:.2f}."
        )
        reasoning = [
            "All Step 1 hard-decline checks passed.",
            routing_rule,
        ]

    return DecisionOutput(
        decision=decision,
        approved_amount=pre["approved_amount"],
        approved_tenure=pre["approved_tenure"],
        interest_rate=pre["interest_rate"],
        disbursement_amount=pre["disbursement_amount"],
        max_approved_amount=pre["max_approved_amount"],
        explanation=explanation,
        reasoning_steps=reasoning,
        confidence_score=1.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────


@track_node("underwriting_decision_engine")
@audit_node(agent_name="decisioning_agent")
def decision_llm_node(state: LoanApplicationState) -> LoanApplicationState:
    decision_output_parser = PydanticOutputParser(pydantic_object=DecisionOutput)

    # ── 1. Pull inputs ───────────────────────────────────────────────
    user_request = state.get("user_request", {}) or {}
    requested_amount = float(user_request.get("amount", 0) or 0)
    requested_tenure = int(user_request.get("tenure", 0) or 0)
    tier = state.get("aggregated_risk_tier") or "F"

    # ── 2. Compute everything deterministically ──────────────────────
    max_approved = _compute_max_approved_amount(state)
    pre = _compute_decision(state, requested_amount, requested_tenure, max_approved)

    step1_outcome = (
        "TRIGGERED: " + ", ".join(pre["step1_triggers"])
        if pre["step1_triggers"]
        else "all checks passed (tier != F, no public-record hard decline, affordability OK)"
    )

    analyzers_ran, analyzers_skipped = _split_active(state)

    # ── 3. Build LLM inputs (pre-computed values + raw context) ──────
    inputs = {
        # Pre-computed (LLM must echo verbatim)
        "pre_decision": pre["decision"],
        "pre_approved_amount": str(pre["approved_amount"]),
        "pre_approved_tenure": str(pre["approved_tenure"]),
        "pre_interest_rate": str(pre["interest_rate"]),
        "pre_disbursement_amount": str(pre["disbursement_amount"]),
        "pre_max_approved_amount": str(pre["max_approved_amount"]),
        "step1_outcome": step1_outcome,
        "routing_rule": pre["routing_rule"],

        # Analyzer participation — drives anti-hallucination instructions in
        # the prompt. Skipped analyzers' *_data slots below render as a
        # literal sentinel so the LLM cannot invent missing values.
        "analyzers_ran": ", ".join(analyzers_ran) or "(none)",
        "analyzers_skipped": ", ".join(analyzers_skipped) or "(none)",

        # Raw context (so the LLM can write a meaningful explanation)
        "aggregated_risk_score": str(state.get("aggregated_risk_score", 0)),
        "aggregated_risk_tier": tier,
        "credit_score_data": _data_for_prompt(state, "credit_score_data", "credit_score"),
        "public_record_data": _data_for_prompt(state, "public_record_data", "public_record"),
        "utilization_data": _data_for_prompt(state, "utilization_data", "utilization"),
        "exposure_data": _data_for_prompt(state, "exposure_data", "exposure"),
        "behavior_data": _data_for_prompt(state, "behavior_data", "behavior"),
        "inquiry_data": _data_for_prompt(state, "inquiry_data", "inquiry"),
        "income_data": _data_for_prompt(state, "income_data", "income"),
        "requested_amount": str(requested_amount),
        "requested_tenure": str(requested_tenure),

        "format_instructions": decision_output_parser.get_format_instructions(),
    }

    # ── 4. Call LLM (only for explanation text) ──────────────────────
    result = execute_llm(
        prompt_template=DECISION_PROMPT,
        inputs=inputs,
        parser=decision_output_parser,
        fallback_result=lambda: _build_fallback_decision_result(pre),
    )

    # ── 5. Build output — Python overrides ALL numeric/decision fields ─
    final_decision = result.model_dump()

    # Trust Python for math + decision; trust LLM for explanation/reasoning_steps.
    final_decision["decision"] = pre["decision"]
    final_decision["approved_amount"] = pre["approved_amount"]
    final_decision["approved_tenure"] = pre["approved_tenure"]
    final_decision["interest_rate"] = pre["interest_rate"]
    final_decision["disbursement_amount"] = pre["disbursement_amount"]
    final_decision["max_approved_amount"] = pre["max_approved_amount"]
    final_decision["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # decision_result drives the conditional router in the graph.
    decision_result = {"decision": pre["decision"]}

    return {
        "final_decision": final_decision,
        "decision_result": decision_result,
    }
