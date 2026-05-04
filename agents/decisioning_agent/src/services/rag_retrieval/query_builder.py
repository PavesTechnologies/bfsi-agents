"""
Build retrieval queries from a CIBIL credit profile.

Two query layers:

1. PROFILE QUERY — one query string summarizing the borrower's credit signals
   (score band, defaults, utilization, DPD, NTC, wilful-defaulter flag).
   Used for the initial pool retrieval against Qdrant.

2. NODE CONCERN QUERIES — short, fixed phrases describing what each analyzer
   node cares about. Used to re-rank the pool per node.
"""

from typing import Any


# Per-node concern queries — phrased to retrieve the SPECIFIC config values
# (thresholds, classification rules, lending limits, weights, factors) that
# each analyzer node needs. These are *config retrieval* queries, not
# borrower-context queries — the borrower data goes in via the prompt's
# INPUT block, the config rules come from these RAG hits.
NODE_CONCERN_QUERIES: dict[str, str] = {
    "credit_score": (
        "Credit score band classification thresholds for personal loan: "
        "PRIME NEAR_PRIME FAIR SUBPRIME score ranges. "
        "Base lending limit by score band in INR. "
        "Risk flag LOW MODERATE HIGH mapping by band. "
        "Score weight in aggregated risk computation."
    ),
    "public_record": (
        "Public record severity classification rules: NONE LOW MODERATE SEVERE. "
        "Adjustment factor by severity level. "
        "Hard decline rules for bankruptcy, suit filed, wilful defaulter, written-off accounts. "
        "Years since bankruptcy threshold for severity downgrade."
    ),
    "credit_utilization": (
        "Revolving credit utilization ratio risk classification thresholds: "
        "EXCELLENT GOOD HIGH CRITICAL utilization percentage bands. "
        "Adjustment factor multiplier by utilization risk tier."
    ),
    "debt_exposure": (
        "Monthly debt obligation thresholds for exposure risk classification: "
        "LOW MODERATE HIGH EXTREME monthly payment amount bands in INR. "
        "Total outstanding debt ceiling. "
        "Monthly EMI estimation rules for tradelines without payment data."
    ),
    "payment_behavior": (
        "Delinquency count and DPD bucket thresholds for behavior risk classification: "
        "EXCELLENT FAIR POOR UNACCEPTABLE behavior score values. "
        "Charge-off identification rules. SMA-0 SMA-1 SMA-2 NPA classification. "
        "30-DPD 60-DPD 90-DPD bucket counting."
    ),
    "inquiry": (
        "Credit inquiry count thresholds in last 12 months for velocity risk: "
        "LOW MODERATE HIGH inquiry-count bands. "
        "Inquiry penalty factor multiplier by velocity risk tier."
    ),
    "income_analysis": (
        "Debt to income DTI ratio thresholds for income risk classification: "
        "LOW MODERATE HIGH UNACCEPTABLE DTI percentage bands. "
        "Affordability cap, FOIR fixed-obligation-to-income ratio. "
        "Missing income handling rules and defaults."
    ),
}


def _extract_utilization_pct(summaries: list) -> float | None:
    """
    summaries is a list of dicts: [{"summaryType": ..., "attributes": [...]}, ...]
    Each `attributes` is itself a list of {"id": "...", "value": "..."} dicts.
    Return the revolvingCreditUtilization percent, or None if not present.
    """
    for entry in summaries:
        if not isinstance(entry, dict):
            continue
        attrs = entry.get("attributes")
        if not isinstance(attrs, list):
            continue
        for attr in attrs:
            if not isinstance(attr, dict):
                continue
            if attr.get("id") == "revolvingCreditUtilization":
                try:
                    return float(str(attr.get("value", "")).replace("%", ""))
                except (TypeError, ValueError):
                    return None
    return None


def _score_band(score: int) -> str:
    if score < 0:
        return "new to credit, no credit history (NTC)"
    if score >= 750:
        return "prime borrower, high credit score"
    if score >= 700:
        return "good credit standing"
    if score >= 650:
        return "fair credit profile, moderate risk"
    if score >= 550:
        return "subprime, elevated risk"
    return "deep subprime, very high risk"


def build_profile_query(masked_data: dict[str, Any]) -> str:
    """
    Compose a one-paragraph natural-language query that captures the
    borrower's salient credit signals. This drives the initial Qdrant
    retrieval; per-node re-ranking refines from there.
    """
    parts: list[str] = []

    # --- Score band ---
    risk_model = masked_data.get("riskModel") or []
    if risk_model:
        try:
            score = int(risk_model[0].get("score", 0))
            parts.append(f"CIBIL score {score} ({_score_band(score)})")
        except (TypeError, ValueError):
            pass

    # --- NTC flag ---
    if masked_data.get("ntcFlag"):
        parts.append("new-to-credit applicant with no prior tradelines")

    # --- Wilful defaulter / suit filed / written-off ---
    if masked_data.get("wilfulDefaulterFlag"):
        parts.append("wilful defaulter flag present")
    if masked_data.get("suitFiledFlag"):
        parts.append("suit filed in court of law")
    if masked_data.get("writtenOffFlag"):
        parts.append("written-off account history")

    # --- Public records ---
    public_records = masked_data.get("publicRecord") or []
    if public_records:
        types = sorted({(r.get("type") or "").upper() for r in public_records if r.get("type")})
        if types:
            parts.append(f"public records: {', '.join(types)}")

    # --- Tradelines ---
    tradelines = masked_data.get("tradeline") or []
    open_count = sum(1 for t in tradelines if t.get("openOrClosed") == "O")
    revolving_count = sum(1 for t in tradelines if t.get("revolvingOrInstallment") == "R")
    if open_count:
        parts.append(f"{open_count} open active tradelines")
    if revolving_count:
        parts.append(f"{revolving_count} revolving credit accounts")

    # --- DPD / delinquencies ---
    delinquencies = 0
    severe_codes = {"SUB", "DBT", "LSS", "XXX", "060", "090", "120", "150", "180"}
    has_severe_dpd = False
    for t in tradelines:
        try:
            delinquencies += int(t.get("delinquencies30Days") or 0)
        except (TypeError, ValueError):
            pass
        for code in (t.get("dpdHistory") or []):
            if str(code) in severe_codes:
                has_severe_dpd = True
                break
    if delinquencies:
        parts.append(f"{delinquencies} delinquency events of 30+ days past due")
    if has_severe_dpd:
        parts.append("severe DPD history including charge-off / sub-standard / loss codes")

    # --- Inquiries ---
    inquiries = masked_data.get("inquiry") or []
    if len(inquiries) >= 4:
        parts.append(f"high enquiry velocity with {len(inquiries)} recent credit pulls")
    elif inquiries:
        parts.append(f"{len(inquiries)} recent credit enquiries")

    # --- Utilization summary ---
    # CIBIL shape: summaries = [{"summaryType": ..., "attributes": [{"id": "...", "value": "..."}, ...]}]
    util_pct = _extract_utilization_pct(masked_data.get("summaries") or [])
    if util_pct is not None:
        if util_pct >= 70:
            parts.append(f"high revolving utilization at {util_pct:.0f}%")
        elif util_pct >= 30:
            parts.append(f"moderate revolving utilization at {util_pct:.0f}%")

    if not parts:
        parts.append("retail loan eligibility assessment")

    return (
        "Indian retail loan underwriting decision for borrower with: "
        + "; ".join(parts)
        + ". Need RBI guidelines and bank policy on eligibility, "
          "exposure limits, DPD classification, and decisioning thresholds."
    )
