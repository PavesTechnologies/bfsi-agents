# src/core/rules/loader.py

import os
import yaml
from typing import Dict
from src.workflows.kyc_engine.rules.validator import validate_rule_set


class RuleLoadError(Exception):
    pass


def load_rule_set(filename: str) -> Dict:
    """
    Loads and validates a YAML rule set file.
    Returns parsed rule dictionary.
    """

    # -----------------------------------------
    # 1. Resolve Path
    # -----------------------------------------
    base_path = "src/workflows/kyc_engine/rules"
    file_path = os.path.join(base_path, filename)

    if not os.path.exists(file_path):
        raise RuleLoadError(f"Rule file not found: {file_path}")

    # -----------------------------------------
    # 2. Load YAML Safely
    # -----------------------------------------
    try:
        with open(file_path, "r") as f:
            rule_set = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise RuleLoadError(f"Invalid YAML syntax: {str(e)}")

    if not isinstance(rule_set, dict):
        raise RuleLoadError("Rule file must contain a valid YAML dictionary")

    # -----------------------------------------
    # 3. Validate Rule Structure
    # -----------------------------------------
    validate_rule_set(rule_set)

    return rule_set