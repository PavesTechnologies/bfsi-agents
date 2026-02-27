#/src/workflows/kyc_engine/rules/validator.py

from typing import Dict, Set


class RuleValidationError(Exception):
    pass


def validate_rule_set(rule_set: Dict) -> None:
    """
    Validates YAML rule set structure and logical consistency.
    Raises RuleValidationError if invalid.
    """

    # -----------------------------------------
    # 1. Required Top-Level Keys
    # -----------------------------------------
    required_keys = {
        "metadata",
        "thresholds",
        "hard_fail_rules",
        "soft_review_rules",
        "weights"
    }

    missing_keys = required_keys - rule_set.keys()
    if missing_keys:
        raise RuleValidationError(
            f"Missing required top-level keys: {missing_keys}"
        )

    # -----------------------------------------
    # 2. Metadata Validation
    # -----------------------------------------
    metadata = rule_set["metadata"]

    if "version" not in metadata:
        raise RuleValidationError("Rule set must include a version")

    if not metadata["version"]:
        raise RuleValidationError("Rule version cannot be empty")

    # -----------------------------------------
    # 3. Validate Rule IDs (No Duplicates)
    # -----------------------------------------
    rule_ids: Set[str] = set()

    for rule in rule_set["hard_fail_rules"]:
        if rule["id"] in rule_ids:
            raise RuleValidationError(f"Duplicate rule ID: {rule['id']}")
        rule_ids.add(rule["id"])

        if rule["outcome"] != "FAIL":
            raise RuleValidationError(
                f"Hard fail rule {rule['id']} must output FAIL"
            )

    for rule in rule_set["soft_review_rules"]:
        if rule["id"] in rule_ids:
            raise RuleValidationError(f"Duplicate rule ID: {rule['id']}")
        rule_ids.add(rule["id"])

        if rule["outcome"] not in {"REVIEW"}:
            raise RuleValidationError(
                f"Soft rule {rule['id']} must output REVIEW"
            )

    # -----------------------------------------
    # 4. Validate Weights
    # -----------------------------------------
    weights = rule_set["weights"]
    total_weight = sum(weights.values())

    if not 0.99 <= total_weight <= 1.01:
        raise RuleValidationError(
            f"Weights must sum to 1.0. Current total: {total_weight}"
        )

    # -----------------------------------------
    # 5. Validate Threshold References
    # -----------------------------------------
    thresholds = rule_set["thresholds"]

    if "soft_signal_threshold" not in thresholds:
        raise RuleValidationError(
            "soft_signal_threshold must be defined in thresholds"
        )

    # -----------------------------------------
    # 6. Logical Conflict Check
    # -----------------------------------------
    hard_outcomes = {r["id"] for r in rule_set["hard_fail_rules"]}
    soft_outcomes = {r["id"] for r in rule_set["soft_review_rules"]}

    intersection = hard_outcomes & soft_outcomes
    if intersection:
        raise RuleValidationError(
            f"Rule IDs cannot exist in both hard and soft sections: {intersection}"
        )

    # If no exception raised → valid