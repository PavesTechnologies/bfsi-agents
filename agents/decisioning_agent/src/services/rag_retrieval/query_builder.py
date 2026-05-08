"""
Build retrieval queries from a CIBIL credit profile.

PROFILE QUERY — one query string summarizing the borrower's credit signals
(score band, defaults, utilization, DPD, NTC, wilful-defaulter flag). Used
for the initial pool retrieval against Qdrant.

(Per-node concern queries used to live here for bank_policies retrieval.
That collection is no longer queried — bank rules now come from the bank-admin
DB via `rules_loader_node`. RBI retrieval uses `retrieve_rbi_common`.)
"""

from typing import Any


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
