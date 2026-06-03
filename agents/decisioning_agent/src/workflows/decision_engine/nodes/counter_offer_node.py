"""
Counter-Offer Structuring Engine
Deterministic Math + LLM Justification

Architecture (three strict layers):
  1. Python computes CO1, CO2, CO3 deterministically before the LLM is called.
  2. LLM receives the pre-computed numbers and writes justification text only.
  3. After the LLM call, every numeric field is overwritten with the Python value.
     The LLM cannot drift any financial figure.

CO1  Reduced amount (qualifying cap), applicant's requested tenure, tier rate.
CO2  Full requested amount at max_tenure, tier rate + 0.5%.  Real EMI always shown.
CO3  Midpoint: (CO1_amount+requested_amount)/2, midpoint(requested_tenure, max_tenure),
     tier rate + 0.25%.  Real EMI always shown; no back-solving.

feasible flag = EMI fits within raw DTI ceiling (not the safety floor).
Recommendation is a Python rule — not an LLM judgement.
"""

from datetime import datetime, timedelta
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.services.rules_db import MissingRuleError
from src.utils.audit_decorator import audit_node
from src.services.llm_executor import execute_llm
from src.services.counter_offer_model.co_math import (
    compute_emi,
    compute_max_affordable_emi,
)
from src.services.counter_offer_model.counter_offer_parser import (
    CounterOfferOption,
    CounterOfferOutput,
    CounterOfferJustificationOutput,
)
from src.services.counter_offer_model.counter_offer_prompt import COUNTER_OFFER_PROMPT
from src.workflows.decision_state import LoanApplicationState


# ─── Defaults (used when rules DB entry is absent) ───────────────────────────

_DEFAULT_MAX_TENURE_MONTHS = 84
_DEFAULT_ORIGINATION_FEE_PCT = 0.02
_DEFAULT_TIER_RATES: dict[str, float] = {"A": 7.5, "B": 10.0, "C": 13.5, "D": 18.0}

# Income-eligibility defaults — must mirror decision_llm_node so the counter
# offer's affordability ceiling matches the one used in the decision.
_DEFAULT_FOIR_BY_TIER: dict[str, float] = {"A": 60, "B": 55, "C": 50, "D": 45, "F": 40}
_DEFAULT_MIN_DISPOSABLE_PCT: float = 10.0

_ALL_ANALYZERS = [
    "credit_score", "public_record", "utilization",
    "exposure", "behavior", "inquiry", "income",
]
_SKIPPED_SENTINEL = "(skipped — analyzer not selected by bank)"


# ─── Helpers: rules + analyzer participation ─────────────────────────────────

def _decision_rules(state: LoanApplicationState) -> dict[str, Any]:
    rules = (state.get("rules_per_node") or {}).get("decision")
    if not rules:
        raise MissingRuleError(rule_key="<decision-bucket>", category="decision")
    return rules


def _split_active(state: LoanApplicationState) -> tuple[list[str], list[str]]:
    active = state.get("active_analyzers")
    if active is None:
        return list(_ALL_ANALYZERS), []
    ran = [a for a in _ALL_ANALYZERS if a in active]
    skipped = [a for a in _ALL_ANALYZERS if a not in active]
    return ran, skipped


def _field_or_skipped(
    state: LoanApplicationState, analyzer_id: str, value: Any, default: Any
) -> str:
    active = state.get("active_analyzers")
    if active is not None and analyzer_id not in active:
        return _SKIPPED_SENTINEL
    return str(value if value is not None else default)


# ─── CO1: Reduced amount, applicant's requested tenure ───────────────────────

def _compute_co1(
    qualifying_cap: float,
    requested_tenure: int,
    tier_rate: float,
    origination_fee_pct: float,
    raw_max_affordable_emi: float,
) -> dict[str, Any]:
    amount = round(qualifying_cap / 1000) * 1000
    emi = compute_emi(amount, tier_rate, requested_tenure)
    disbursement = round(amount * (1 - origination_fee_pct), 2)
    total = round(emi * requested_tenure, 2)
    return {
        "option_id": "CO1",
        "label": "Reduced Amount",
        "proposed_amount": amount,
        "proposed_tenure_months": requested_tenure,
        "proposed_interest_rate": tier_rate,
        "monthly_payment_emi": emi,
        "disbursement_amount": disbursement,
        "total_repayment": total,
        "affordability_headroom_pct": _headroom_pct(raw_max_affordable_emi, emi),
        "is_recommended": False,
        "feasible": True,
        "justification": "",
    }


# ─── Headroom helper ─────────────────────────────────────────────────────────

def _headroom_pct(raw_max_affordable_emi: float, emi: float) -> float:
    """
    Returns affordability headroom as a percentage.

    When raw_max_affordable_emi ≤ 0 the applicant is already over their DTI
    ceiling before this loan, so headroom is capped at -100 % rather than
    dividing by the safety-floor value (which would produce nonsense like
    -352,951 %).
    """
    if raw_max_affordable_emi <= 0:
        return -100.0
    return round(((raw_max_affordable_emi - emi) / raw_max_affordable_emi) * 100, 2)


# ─── CO2: Full amount at maximum tenure ──────────────────────────────────────

def _compute_co2(
    requested_amount: float,
    tier_rate: float,
    raw_max_affordable_emi: float,
    origination_fee_pct: float,
    max_tenure: int,
) -> dict[str, Any]:
    """
    Offer the full requested amount stretched to the longest permitted tenure.

    We no longer back-solve the tenure from the affordability ceiling because
    when max_affordable_emi is at its safety floor (1.0) any real loan is
    "infeasible" — producing tenure=0 and all-zero values that confuse the
    bank admin.  Instead we always compute real numbers and let the `feasible`
    flag signal whether the EMI fits within the applicant's DTI ceiling.
    """
    co2_rate = round(tier_rate + 0.5, 2)
    tenure = max_tenure
    emi = compute_emi(requested_amount, co2_rate, tenure)
    disbursement = round(requested_amount * (1 - origination_fee_pct), 2)
    total = round(emi * tenure, 2)
    feasible = raw_max_affordable_emi > 0 and emi <= raw_max_affordable_emi
    return {
        "option_id": "CO2",
        "label": "Extended Tenure",
        "proposed_amount": requested_amount,
        "proposed_tenure_months": tenure,
        "proposed_interest_rate": co2_rate,
        "monthly_payment_emi": emi,
        "disbursement_amount": disbursement,
        "total_repayment": total,
        "affordability_headroom_pct": _headroom_pct(raw_max_affordable_emi, emi),
        "is_recommended": False,
        "feasible": feasible,
        "justification": "",
    }


# ─── CO3: Algorithmic midpoint ────────────────────────────────────────────────

def _compute_co3(
    co1_amount: float,
    requested_amount: float,
    requested_tenure: int,
    tier_rate: float,
    origination_fee_pct: float,
    raw_max_affordable_emi: float,
    max_tenure: int,
) -> dict[str, Any]:
    """
    Balanced midpoint between CO1 and CO2.

    Amount  = midpoint(CO1_amount, requested_amount) rounded to nearest ₹1,000.
    Tenure  = midpoint(requested_tenure, max_tenure)  rounded to nearest 6 months.

    We no longer back-solve the amount from the affordability ceiling — that
    produced ₹0 whenever the floor value (1.0) was in effect.  Real numbers
    are always computed; `feasible` signals whether the EMI fits the DTI ceiling.
    """
    co3_rate = round(tier_rate + 0.25, 2)

    # Amount: midpoint of qualifying cap (CO1) and full requested amount (CO2).
    co3_amount = round(((co1_amount + requested_amount) / 2) / 1000) * 1000

    # Tenure: midpoint of requested tenure (CO1) and max_tenure (CO2 always uses max_tenure).
    raw_tenure = (requested_tenure + max_tenure) / 2
    co3_tenure = round(raw_tenure / 6) * 6
    co3_tenure = max(co3_tenure, max(requested_tenure, 6))
    co3_tenure = min(co3_tenure, max_tenure)

    emi = compute_emi(co3_amount, co3_rate, co3_tenure)
    disbursement = round(co3_amount * (1 - origination_fee_pct), 2)
    total = round(emi * co3_tenure, 2)
    feasible = raw_max_affordable_emi > 0 and emi <= raw_max_affordable_emi
    return {
        "option_id": "CO3",
        "label": "Balanced Option",
        "proposed_amount": co3_amount,
        "proposed_tenure_months": co3_tenure,
        "proposed_interest_rate": co3_rate,
        "monthly_payment_emi": emi,
        "disbursement_amount": disbursement,
        "total_repayment": total,
        "affordability_headroom_pct": _headroom_pct(raw_max_affordable_emi, emi),
        "is_recommended": False,
        "feasible": feasible,
        "justification": "",
    }


# ─── Recommendation: Python rule, not LLM ────────────────────────────────────

def _compute_recommendation(
    co2: dict[str, Any],
    co3: dict[str, Any],
    max_tenure_threshold: int = 60,
) -> tuple[str, str]:
    """
    Priority order:
      CO2  — applicant gets the full amount and the tenure is reasonable (≤ threshold).
      CO3  — CO2 requires a very long tenure OR CO2 is over-DTI but CO3 is feasible.
      CO2  — CO2 feasible + long tenure but CO3 is also over-DTI (CO2 > CO3 in loan size).
      CO1  — neither CO2 nor CO3 are within DTI ceiling; CO1 is the maximum viable offer.
    """
    if co2["feasible"] and co2["proposed_tenure_months"] <= max_tenure_threshold:
        return (
            "CO2",
            "The applicant qualifies for the full requested amount within a "
            "reasonable repayment window.",
        )
    if co3["feasible"]:
        return (
            "CO3",
            "CO3 offers the best balance between loan size and monthly commitment "
            "given the applicant's current income and obligations.",
        )
    if co2["feasible"]:
        # CO2 is affordable but requires a longer-than-preferred tenure; CO3 is not
        # feasible, so CO2 is still the better option over CO1 for loan size.
        return (
            "CO2",
            "The full requested amount is affordable but requires an extended tenure; "
            "CO3 is not viable within the applicant's DTI ceiling.",
        )
    return (
        "CO1",
        "The applicant's income profile cannot support the full requested amount "
        "at any feasible tenure; CO1 represents the maximum viable offer.",
    )


# ─── Fallback justification (used when the LLM call fails entirely) ──────────

def _build_fallback_justification(
    co2_feasible: bool,
    recommended_id: str,
) -> CounterOfferJustificationOutput:
    co2_just = (
        "Extending the repayment period reduces the monthly commitment to a level "
        "that fits within the applicant's current income and obligations."
        if co2_feasible
        else
        "The full requested amount cannot be supported at any repayment tenure "
        "given the applicant's current income and existing obligations."
    )
    return CounterOfferJustificationOutput(
        counter_offer_logic=(
            "The original loan request was not approved because the requested amount "
            "exceeds the applicant's qualifying limit based on their income profile "
            "and existing financial obligations."
        ),
        co1_justification=(
            "This offer reduces the principal to the level the applicant currently qualifies "
            "for while keeping the original repayment period intact."
        ),
        co2_justification=co2_just,
        co3_justification=(
            "This option partially reduces the loan amount and moderately extends the tenure, "
            "providing a balanced middle path between maximum loan size and minimum monthly outflow."
        ),
        recommendation_rationale=(
            f"{recommended_id} is recommended as the best fit for the applicant's "
            "current financial profile."
        ),
        confidence_score=0.0,
    )


# ─── LLM input builder ───────────────────────────────────────────────────────

def _build_llm_inputs(
    state: LoanApplicationState,
    co1: dict[str, Any],
    co2: dict[str, Any],
    co3: dict[str, Any],
    recommended_id: str,
    recommendation_reason: str,
    raw_max_affordable_emi: float,
    monthly_income: float,
    monthly_obligations: float,
    qualifying_cap: float,
    requested_amount: float,
    requested_tenure: int,
    format_instructions: str,
) -> dict[str, str]:
    analyzers_ran, analyzers_skipped = _split_active(state)
    income_data = state.get("income_data") or {}
    credit_score_data = state.get("credit_score_data") or {}

    def _fmt(v: float) -> str:
        return f"{v:,.2f}"

    return {
        # Profile
        "monthly_income": _fmt(monthly_income),
        "existing_monthly_obligations": _fmt(monthly_obligations),
        "max_affordable_emi": _fmt(raw_max_affordable_emi),
        "estimated_dti": _field_or_skipped(state, "income", income_data.get("estimated_dti"), "N/A"),
        "risk_tier": str(state.get("aggregated_risk_tier") or "D"),
        "score_band": str(credit_score_data.get("score_band") or "FAIR"),
        "qualifying_cap": _fmt(qualifying_cap),
        "requested_amount": _fmt(requested_amount),
        "requested_tenure": str(requested_tenure),
        "analyzers_ran": ", ".join(analyzers_ran) or "(none)",
        "analyzers_skipped": ", ".join(analyzers_skipped) or "(none)",
        # CO1
        "co1_amount": _fmt(co1["proposed_amount"]),
        "co1_tenure": str(co1["proposed_tenure_months"]),
        "co1_rate": str(co1["proposed_interest_rate"]),
        "co1_emi": _fmt(co1["monthly_payment_emi"]),
        "co1_disbursement": _fmt(co1["disbursement_amount"]),
        "co1_total": _fmt(co1["total_repayment"]),
        "co1_headroom_pct": str(co1["affordability_headroom_pct"]),
        # CO2 — render N/A fields when infeasible so LLM cannot hallucinate numbers
        "co2_feasible": str(co2["feasible"]),
        "co2_amount": _fmt(co2["proposed_amount"]),
        "co2_tenure": str(co2["proposed_tenure_months"]) if co2["feasible"] else "N/A",
        "co2_rate": str(co2["proposed_interest_rate"]),
        "co2_emi": _fmt(co2["monthly_payment_emi"]) if co2["feasible"] else "N/A",
        "co2_disbursement": _fmt(co2["disbursement_amount"]) if co2["feasible"] else "N/A",
        "co2_total": _fmt(co2["total_repayment"]) if co2["feasible"] else "N/A",
        "co2_headroom_pct": str(co2["affordability_headroom_pct"]) if co2["feasible"] else "N/A",
        # CO3
        "co3_amount": _fmt(co3["proposed_amount"]),
        "co3_tenure": str(co3["proposed_tenure_months"]),
        "co3_rate": str(co3["proposed_interest_rate"]),
        "co3_emi": _fmt(co3["monthly_payment_emi"]),
        "co3_disbursement": _fmt(co3["disbursement_amount"]),
        "co3_total": _fmt(co3["total_repayment"]),
        "co3_headroom_pct": str(co3["affordability_headroom_pct"]),
        # Recommendation
        "recommended_option_id": recommended_id,
        "recommendation_reason": recommendation_reason,
        "format_instructions": format_instructions,
    }


# ─── Main node ────────────────────────────────────────────────────────────────

@track_node("counter_offer_engine")
@audit_node(agent_name="decisioning_agent")
def counter_offer_node(state: LoanApplicationState) -> LoanApplicationState:
    """
    Deterministic counter-offer structuring node.

    Python computes all three offers; LLM writes justification text only.
    After the LLM call, every numeric field is overwritten with Python values.
    """
    justification_parser = PydanticOutputParser(
        pydantic_object=CounterOfferJustificationOutput
    )

    # ── 1. Extract inputs from state ────────────────────────────────────
    user_request        = state.get("user_request") or {}
    income_data         = state.get("income_data") or {}
    exposure_data       = state.get("exposure_data") or {}
    final_decision      = state.get("final_decision") or {}
    decision_rules      = _decision_rules(state)

    requested_amount    = float(user_request.get("amount", 0))
    requested_tenure    = int(user_request.get("tenure", 0))

    # monthly_income lives in bank_statement_summary, not income_data
    monthly_income      = float(
        (state.get("bank_statement_summary") or {}).get("monthly_income", 0) or 0
    )
    monthly_obligations = float(exposure_data.get("monthly_obligation_estimate", 0) or 0)
    estimated_dti       = float(income_data.get("estimated_dti", 0) or 0)

    tier                = str(state.get("aggregated_risk_tier") or "D")
    qualifying_cap      = float(final_decision.get("max_approved_amount", 0))

    tier_rates          = decision_rules.get("tier_interest_rates") or _DEFAULT_TIER_RATES
    tier_rate           = float(tier_rates.get(tier, _DEFAULT_TIER_RATES["D"]))
    origination_fee_pct = float(decision_rules.get("origination_fee_pct", _DEFAULT_ORIGINATION_FEE_PCT))
    max_tenure          = int(decision_rules.get("max_tenure_months", _DEFAULT_MAX_TENURE_MONTHS))

    # Affordability ceiling: tier-driven FOIR % of income minus existing
    # obligations, floored at min_disposable_pct% of income (never ≤ 0 when
    # income > 0). Uses the SAME helper + rules as the decision node so the
    # counter offer's feasibility checks match the qualifying cap exactly.
    foir_by_tier        = decision_rules.get("foir_threshold_by_tier") or _DEFAULT_FOIR_BY_TIER
    foir_pct            = float(foir_by_tier.get(tier, _DEFAULT_FOIR_BY_TIER.get(tier, 40)))
    min_disposable_pct  = float(
        decision_rules.get("min_disposable_income_pct", _DEFAULT_MIN_DISPOSABLE_PCT)
    )
    raw_max_affordable_emi = compute_max_affordable_emi(
        monthly_income, monthly_obligations, foir_pct, min_disposable_pct
    )

    # ── 2. Compute all three offers (Python — deterministic) ─────────────
    co1 = _compute_co1(
        qualifying_cap, requested_tenure, tier_rate, origination_fee_pct,
        raw_max_affordable_emi,
    )
    co2 = _compute_co2(
        requested_amount, tier_rate, raw_max_affordable_emi, origination_fee_pct, max_tenure,
    )
    co3 = _compute_co3(
        co1["proposed_amount"], requested_amount, requested_tenure,
        tier_rate, origination_fee_pct, raw_max_affordable_emi, max_tenure,
    )

    # ── 3. Compute recommendation (Python — rule-based) ─────────────────
    recommended_id, recommendation_reason = _compute_recommendation(co2, co3)

    co1["is_recommended"] = (recommended_id == "CO1")
    co2["is_recommended"] = (recommended_id == "CO2")
    co3["is_recommended"] = (recommended_id == "CO3")

    # ── 4. Call LLM — justification text only ────────────────────────────
    llm_inputs = _build_llm_inputs(
        state, co1, co2, co3, recommended_id, recommendation_reason,
        raw_max_affordable_emi, monthly_income, monthly_obligations,
        qualifying_cap, requested_amount, requested_tenure,
        justification_parser.get_format_instructions(),
    )

    justification = execute_llm(
        prompt_template=COUNTER_OFFER_PROMPT,
        inputs=llm_inputs,
        parser=justification_parser,
        fallback_result=lambda: _build_fallback_justification(co2["feasible"], recommended_id),
    )

    # ── 5. Merge LLM justification text into Python-computed offer dicts ──
    co1["justification"] = justification.co1_justification
    co2["justification"] = justification.co2_justification
    co3["justification"] = justification.co3_justification

    # ── 6. Build final output ─────────────────────────────────────────────
    # Numeric fields come exclusively from Python.
    # Text fields (justification, logic, rationale) come from the LLM.
    result = CounterOfferOutput(
        original_request_dti=estimated_dti,
        max_affordable_emi=round(raw_max_affordable_emi, 2),
        monthly_income=monthly_income,
        existing_monthly_obligations=monthly_obligations,
        qualifying_cap=qualifying_cap,
        counter_offer_logic=justification.counter_offer_logic,
        generated_options=[
            CounterOfferOption(**co1),
            CounterOfferOption(**co2),
            CounterOfferOption(**co3),
        ],
        recommended_option_id=recommended_id,
        recommendation_rationale=justification.recommendation_rationale,
        confidence_score=justification.confidence_score,
        expires_at=(datetime.now() + timedelta(days=10)).isoformat(),
    )

    counter_offer_data = result.model_dump()
    counter_offer_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"counter_offer_data": counter_offer_data}
