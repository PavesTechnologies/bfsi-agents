from typing import Dict, Any, List


class RuleExecutionError(Exception):
    pass


def _resolve_value(path: str, signals: Dict[str, Dict]) -> Any:
    """
    Resolves dotted path like 'aml.ofac_match'
    """
    parts = path.split(".")
    root = parts[0]

    if root not in signals:
        raise RuleExecutionError(f"Invalid signal root: {root}")

    value = signals[root]
    for p in parts[1:]:
        value = value.get(p)

    return value


def _evaluate_condition(condition: Dict, signals: Dict, thresholds: Dict) -> bool:

    # OR logic
    if "any" in condition:
        for sub_condition in condition["any"]:
            if _evaluate_condition(sub_condition, signals, thresholds):
                return True
        return False

    # Single condition
    for key, expected in condition.items():
        actual_value = _resolve_value(key, signals)

        # If value missing → condition cannot be satisfied
        if actual_value is None:
            return False

        # Threshold-based condition
        if isinstance(expected, str) and expected.startswith("<"):
            threshold_key = expected.replace("<", "").strip().split(".")[-1]
            threshold_value = thresholds.get(threshold_key)

            # Defensive check
            if threshold_value is None:
                raise RuleExecutionError(
                    f"Threshold '{threshold_key}' not defined in rule set"
                )

            return float(actual_value) < float(threshold_value)

        # Direct equality
        return actual_value == expected

    return False


def execute_rules(rule_set: Dict, signals: Dict[str, Dict]) -> Dict:
    """
    Executes rule engine logic.
    """

    thresholds = rule_set.get("thresholds", {})
    triggered_rules: List[str] = []
    soft_flags: List[str] = []

    # -----------------------------------------
    # 1. Evaluate Hard Fail Rules (Priority Order)
    # -----------------------------------------
    hard_rules = sorted(
        rule_set.get("hard_fail_rules", []),
        key=lambda r: r.get("priority", 999)
    )

    for rule in hard_rules:
        if _evaluate_condition(rule["condition"], signals, thresholds):
            triggered_rules.append(rule["id"])
            return {
                "final_status": "FAIL",
                "triggered_rules": triggered_rules,
                "soft_flags": []
            }

    # -----------------------------------------
    # 2. Evaluate Soft Review Rules
    # -----------------------------------------
    for rule in rule_set.get("soft_review_rules", []):
        if _evaluate_condition(rule["condition"], signals, thresholds):
            soft_flags.append(rule["id"])

    # -----------------------------------------
    # 3. Determine Final Status
    # -----------------------------------------
    soft_threshold = thresholds.get("soft_signal_threshold", 1)

    if len(soft_flags) >= soft_threshold:
        return {
            "final_status": "NEEDS_HUMAN_REVIEW",
            "triggered_rules": soft_flags,
            "soft_flags": soft_flags
        }

    return {
        "final_status": "PASS",
        "triggered_rules": [],
        "soft_flags": []
    }