"""Second-pass verification for AI-assisted explanations."""


def critique_explanation(
    *,
    explanation_text: str,
    reason_keys: list[str],
    cited_sections: list[str],
    policy_evidence: list[dict],
) -> dict:
    failures = []
    evidence_sections = {item.get("section_id") for item in policy_evidence}

    if not explanation_text or len(explanation_text.strip()) < 20:
        failures.append("Explanation text is missing or too short.")

    for cited_section in cited_sections:
        if cited_section not in evidence_sections:
            failures.append(f"Cited section {cited_section} was not present in retrieved evidence.")

    if any(reason_key and reason_key.split("_")[0].lower() not in explanation_text.lower() for reason_key in reason_keys if reason_key):
        # Keep the check simple and conservative so unsupported text falls back safely.
        failures.append("Explanation may not clearly reflect selected reason keys.")

    return {
        "passed": not failures,
        "failures": failures,
    }
