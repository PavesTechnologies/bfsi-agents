"""Utilities for loading underwriting policy configuration."""

from functools import lru_cache
from pathlib import Path

import yaml

from src.policy.policy_types import UnderwritingPolicy


def _policy_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "bank_risk_config.yaml"


@lru_cache
def load_policy_config() -> dict:
    with _policy_path().open("r", encoding="utf-8") as policy_file:
        return yaml.safe_load(policy_file)


@lru_cache
def load_underwriting_policy() -> UnderwritingPolicy:
    return UnderwritingPolicy.model_validate(load_policy_config())
