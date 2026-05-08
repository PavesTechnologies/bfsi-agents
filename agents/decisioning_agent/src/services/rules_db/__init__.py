"""DB-backed bank-rule loader.

Reads `bank_rules` from the bank-admin DB (read-only) so analyzer nodes can
inject live, HITL-approved policy values into their prompts and deterministic
logic — replacing the per-node bank_policies RAG retrieval.
"""
from src.services.rules_db.errors import MissingRuleError
from src.services.rules_db.formatter import format_rules_for_prompt
from src.services.rules_db.repository import fetch_rules_for_categories

__all__ = [
    "MissingRuleError",
    "fetch_rules_for_categories",
    "format_rules_for_prompt",
]
