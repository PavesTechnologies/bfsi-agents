def parse_llm_output(text: str) -> dict | None:
    """
    Enforces strict LLM contract.
    Expected format:

    ISSUE: <one sentence>
    ACTION: <one concrete action>

    Returns None if output is invalid or useless.
    """

    if not text:
        return None

    text = text.strip()

    if text == "NONE":
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    issue = None
    action = None

    for line in lines:
        if line.startswith("ISSUE:"):
            issue = line[len("ISSUE:"):].strip()
        elif line.startswith("ACTION:"):
            action = line[len("ACTION:"):].strip()

    if not issue or not action:
        return None

    return {
        "issue": issue,
        "action": action,
    }
