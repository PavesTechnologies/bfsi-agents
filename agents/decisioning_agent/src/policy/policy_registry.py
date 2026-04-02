"""Active policy selection and registry helpers."""

from functools import lru_cache

from src.policy.policy_loader import load_underwriting_policy
from src.policy.policy_types import UnderwritingPolicy


@lru_cache
def get_active_policy(
    product_code: str = "UNSECURED_PERSONAL_LOAN",
    policy_version: str | None = None,
) -> UnderwritingPolicy:
    policy = load_underwriting_policy()
    if product_code != policy.product_eligibility.product_code:
        raise ValueError(f"Unsupported product_code: {product_code}")
    if policy_version and policy.bank.policy_version != policy_version:
        raise ValueError(
            f"Requested policy_version {policy_version} does not match active policy {policy.bank.policy_version}"
        )
    return policy
