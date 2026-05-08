"""Read-only access to bank_rules grouped by rule_categories.name.

The repository only SELECTs — writes happen exclusively through
bank-admin-service's RuleService with its HITL approval workflow.
"""
from typing import Any

from sqlalchemy import text

from src.services.rules_db.client import get_rules_session


_FETCH_SQL = text(
    """
    SELECT rc.name AS category_name,
           br.rule_key,
           br.current_value
      FROM bank_rules br
      JOIN rule_categories rc ON rc.id = br.category_id
     WHERE br.is_active = true
       AND rc.name = ANY(:names)
    """
)


async def fetch_rules_for_categories(
    names: list[str],
) -> dict[str, dict[str, Any]]:
    """Return `{category_name: {rule_key: value}}` for the given category names.

    `value` is the unwrapped JSON inside `current_value["value"]` — the seed
    convention used by every row in 001/003 migrations. Categories that exist
    but have no active rules return as `{}`. Categories that don't exist at
    all return as `{}` as well (caller validates required keys).
    """
    if not names:
        return {}

    grouped: dict[str, dict[str, Any]] = {n: {} for n in names}

    async with get_rules_session() as session:
        result = await session.execute(_FETCH_SQL, {"names": names})
        for row in result.mappings().all():
            cat = row["category_name"]
            key = row["rule_key"]
            current_value = row["current_value"] or {}
            value = current_value.get("value") if isinstance(current_value, dict) else current_value
            grouped.setdefault(cat, {})[key] = value

    return grouped
