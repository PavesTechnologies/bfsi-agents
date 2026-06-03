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
from src.services.counter_offer_model.co_math import (
    compute_max_affordable_emi,
    compute_max_principal,
)
from src.services.decision_model.decision_parser import DecisionOutput
from src.services.decision_model.decision_prompt import DECISION_PROMPT
from src.services.llm_executor import execute_llm
from src.services.rules_db import MissingRuleError
from src.utils.audit_decorator import audit_node
from src.workflows.decision_state import LoanApplicationState


# Code-baked defaults for the income-eligibility rules (migration 005/006).
# Used only when a rule is absent from the DB so the engine never crashes or
# zeroes out in an environment that hasn't been migrated yet.
_DEFAULT_FOIR_BY_TIER: dict[str, float] = {"A": 60, "B": 55, "C": 50, "D": 45, "F": 40}
_DEFAULT_INCOME_MULTIPLE_BY_TIER: dict[str, float] = {"A": 24, "B": 20, "C": 15, "D": 10, "F": 0}
_DEFAULT_MIN_DISPOSABLE_PCT: float = 10.0
_DEFAULT_COUNTER_OFFER_OVERAGE_PCT: float = 30.0


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
    Income-driven qualifying cap (replaces the old flat base_limit_band approach).

      1. max_affordable_emi = FOIR(tier)% of monthly income − existing obligations,
         floored at min_disposable_pct% of income (never ≤ 0 when income > 0).
      2. principal_from_emi = largest loan whose EMI ≤ that ceiling, at the tier
         interest rate over the requested tenure (reducing-balance back-solve).
      3. adjusted = principal_from_emi × public-record × utilization × inquiry
         factors (the existing credit-profile multipliers).
      4. income_ceiling = monthly income × 12 × income-multiple(tier).
      max_approved = min(adjusted, income_ceiling).

    Returns 0.0 when monthly income or requested tenure is missing/zero — the
    caller treats a 0 cap as a decline (no qualifying capacity).
    """
    decision_rules = _decision_rules(state)
    tier = str(state.get("aggregated_risk_tier") or "F")

    monthly_income = float(
        (state.get("bank_statement_summary") or {}).get("monthly_income", 0) or 0
    )
    existing_obligations = float(
        (state.get("exposure_data") or {}).get("monthly_obligation_estimate", 0) or 0
    )
    requested_tenure = int((state.get("user_request") or {}).get("tenure", 0) or 0)

    if monthly_income <= 0 or requested_tenure <= 0:
        return 0.0

    # Step 1 — tier-driven FOIR affordability ceiling (with floor).
    foir_by_tier = decision_rules.get("foir_threshold_by_tier") or _DEFAULT_FOIR_BY_TIER
    foir_pct = float(foir_by_tier.get(tier, _DEFAULT_FOIR_BY_TIER.get(tier, 40)))
    min_disposable_pct = float(
        decision_rules.get("min_disposable_income_pct", _DEFAULT_MIN_DISPOSABLE_PCT)
    )
    max_affordable_emi = compute_max_affordable_emi(
        monthly_income, existing_obligations, foir_pct, min_disposable_pct
    )
    if max_affordable_emi <= 0:
        return 0.0

    # Step 2 — back-solve the largest principal that fits the EMI ceiling.
    tier_rate = _interest_rate_for_tier(tier, decision_rules["tier_interest_rates"])
    monthly_rate = tier_rate / 12.0 / 100.0
    principal_from_emi = compute_max_principal(
        max_affordable_emi, monthly_rate, requested_tenure
    )

    # Step 3 — credit-profile factors shrink the income-derived limit.
    pr_factor = float(
        (state.get("public_record_data") or {}).get("public_record_adjustment_factor") or 1.0
    )
    util_factor = float(
        (state.get("utilization_data") or {}).get("utilization_adjustment_factor") or 1.0
    )
    inq_factor = float(
        (state.get("inquiry_data") or {}).get("inquiry_penalty_factor") or 1.0
    )
    adjusted = principal_from_emi * pr_factor * util_factor * inq_factor

    # Step 4 — secondary ceiling: loan as a multiple of annual income.
    multiple_by_tier = (
        decision_rules.get("income_multiple_cap_by_tier") or _DEFAULT_INCOME_MULTIPLE_BY_TIER
    )
    multiple = float(
        multiple_by_tier.get(tier, _DEFAULT_INCOME_MULTIPLE_BY_TIER.get(tier, 0))
    )
    income_ceiling = monthly_income * 12.0 * multiple

    return round(min(adjusted, income_ceiling), 2)


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

    # No qualifying capacity — income too low / obligations too high to support
    # any loan. Not a Step 1 flag; it's derived from the income-based cap.
    if max_approved_amount <= 0:
        return {
            "decision": "DECLINE",
            "approved_amount": 0.0,
            "approved_tenure": 0,
            "interest_rate": 0.0,
            "disbursement_amount": 0.0,
            "max_approved_amount": max_approved_amount,
            "step1_triggers": [],
            "routing_rule": (
                "DECLINE — no qualifying amount: income capacity insufficient "
                "to support any loan at the requested tenure"
            ),
        }

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

    # requested > max → counter-offer, UNLESS the request exceeds the cap by more
    # than the allowed overage (then it's too far out of reach → decline).
    overage_pct = float(
        decision_rules.get("counter_offer_overage_pct", _DEFAULT_COUNTER_OFFER_OVERAGE_PCT)
    )
    overage_ceiling = round(max_approved_amount * (1 + overage_pct / 100.0), 2)

    if requested_amount <= overage_ceiling:
        return {
            "decision": "COUNTER_OFFER",
            "approved_amount": 0.0,
            "approved_tenure": 0,
            "interest_rate": interest_rate,
            "disbursement_amount": 0.0,
            "max_approved_amount": max_approved_amount,
            "step1_triggers": [],
            "routing_rule": (
                f"RULE B: max ({max_approved_amount:.2f}) < requested "
                f"({requested_amount:.2f}) <= overage ceiling "
                f"({overage_ceiling:.2f} = {100 + overage_pct:.0f}% of cap) → COUNTER_OFFER"
            ),
        }

    return {
        "decision": "DECLINE",
        "approved_amount": 0.0,
        "approved_tenure": 0,
        "interest_rate": 0.0,
        "disbursement_amount": 0.0,
        "max_approved_amount": max_approved_amount,
        "step1_triggers": [],
        "routing_rule": (
            f"DECLINE — requested ({requested_amount:.2f}) exceeds "
            f"{100 + overage_pct:.0f}% of the qualifying cap "
            f"({max_approved_amount:.2f}); over the {overage_pct:.0f}% counter-offer overage limit"
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
        # Step 1 declines list explicit triggers; income-capacity / overage
        # declines carry their reason in routing_rule instead.
        reason = ", ".join(triggers) if triggers else routing_rule
        explanation = f"Application declined. {reason}."
        reasoning = [
            "DETERMINISTIC DECLINE — LLM explanation unavailable.",
            routing_rule,
        ] + triggers
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
