"""Simple local retrieval for policy-grounded explanations."""

from src.services.policy_retrieval.indexer import build_policy_index


QUERY_HINTS = {
    "DTI_HIGH": ["dti", "debt-to-income", "income verification"],
    "INCOME_UNVERIFIED": ["income verification", "unverifiable income"],
    "BANKRUPTCY_RECENT": ["bankruptcy", "public record", "hard decline"],
    "PUBLIC_RECORD_SEVERE": ["public record", "hard decline"],
    "UTILIZATION_HIGH": ["utilization", "revolving"],
    "EXPOSURE_HIGH": ["exposure", "obligations", "debt"],
    "INQUIRIES_EXCESSIVE": ["inquiries", "credit seeking"],
    "PAYMENT_BEHAVIOR_POOR": ["delinquency", "payment behavior", "charge-off"],
    "CREDIT_HISTORY_INSUFFICIENT": ["credit history", "tradeline", "thin file"],
    "THIN_FILE": ["thin file", "tradeline"],
    "RISK_TIER_F": ["overall risk", "policy threshold"],
}


def retrieve_policy_evidence(
    *,
    reason_keys: list[str],
    key_factors: list[str] | None = None,
    max_chunks: int = 3,
) -> list[dict]:
    index = build_policy_index()
    key_factors = key_factors or []
    hints = set()
    for reason_key in reason_keys:
        hints.update(QUERY_HINTS.get(reason_key, []))
    for factor in key_factors:
        hints.update(word.lower() for word in str(factor).split())

    scored = []
    for chunk in index:
        content = chunk["content"].lower()
        score = sum(1 for hint in hints if hint in content)
        if score:
            scored.append((score, chunk))

    if not scored:
        return index[:max_chunks]

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:max_chunks]]
