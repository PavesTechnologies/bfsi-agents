"""reconcile income-based eligibility rules on already-005 databases

Revision ID: 006_reconcile_income_eligibility
Revises: 005_income_based_eligibility
Create Date: 2026-06-03

Why this exists
---------------
The shared database was stamped at 005_income_based_eligibility by an earlier
checkout that seeded only a PARTIAL / variant rule set:

    foir_threshold_by_tier      = {"A":55,"B":50,"C":45,"D":40}   (no F tier)
    income_multiple_cap_by_tier = {"A":24,"B":20,"C":15,"D":10}   (no F tier)
    min_disposable_income_pct   = (absent)
    counter_offer_overage_pct   = (absent)

Because the DB already reports revision 005, the canonical 005 file in this
repo never runs against it. This migration brings any such database up to the
intended canonical set, and is fully idempotent:

  * INSERTs the two missing rules only WHERE NOT EXISTS.
  * UPDATEs the two tier rules to the canonical values (adds the F tier).

On a fresh database (where 005 already inserted all four rules with the
canonical values), every statement here is a harmless no-op.
"""
from typing import Sequence, Union
from alembic import op


revision: str = "006_reconcile_income_eligibility"
down_revision: Union[str, Sequence[str], None] = "005_income_based_eligibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Rules this migration may INSERT (only the two that can be missing).
_INSERTED_RULE_KEYS: tuple[str, ...] = (
    "min_disposable_income_pct",
    "counter_offer_overage_pct",
)


def upgrade() -> None:
    # 1) Align the two tier rules to the canonical values (idempotent: sets the
    #    same values on a fresh DB, adds the F tier on a partial DB). Both
    #    current_value and default_value are aligned.
    op.execute(
        r"""
        UPDATE bank_rules
        SET current_value = $j$ {"value": {"A": 60, "B": 55, "C": 50, "D": 45, "F": 40}} $j$::jsonb,
            default_value = $j$ {"value": {"A": 60, "B": 55, "C": 50, "D": 45, "F": 40}} $j$::jsonb
        WHERE rule_key = 'foir_threshold_by_tier'
        """
    )
    op.execute(
        r"""
        UPDATE bank_rules
        SET current_value = $j$ {"value": {"A": 24, "B": 20, "C": 15, "D": 10, "F": 0}} $j$::jsonb,
            default_value = $j$ {"value": {"A": 24, "B": 20, "C": 15, "D": 10, "F": 0}} $j$::jsonb
        WHERE rule_key = 'income_multiple_cap_by_tier'
        """
    )

    # 2) Insert the affordability floor only if absent.
    op.execute(
        r"""
        INSERT INTO bank_rules (
            category_id, rule_key, display_name, description,
            current_value, default_value, data_type, validation_schema,
            risk_level, requires_approval
        )
        SELECT
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'min_disposable_income_pct',
            'Minimum Disposable Income Floor (%% of Income)',
            'Affordability floor. The max affordable EMI never drops below this percent of gross monthly income, even when existing obligations are high. Guarantees affordability is never zero for an applicant who has income.',
            '{"value": 10}'::jsonb, '{"value": 10}'::jsonb,
            'number', '{"min": 0, "max": 100}'::jsonb, 'high', true
        WHERE NOT EXISTS (
            SELECT 1 FROM bank_rules WHERE rule_key = 'min_disposable_income_pct'
        )
        """
    )

    # 3) Insert the counter-offer overage limit only if absent.
    op.execute(
        r"""
        INSERT INTO bank_rules (
            category_id, rule_key, display_name, description,
            current_value, default_value, data_type, validation_schema,
            risk_level, requires_approval
        )
        SELECT
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'counter_offer_overage_pct',
            'Counter-Offer Overage Limit (%% over cap)',
            'If the requested amount exceeds the max approvable amount by more than this percent, the application is declined instead of generating a counter offer. Example: 30 means requests up to 130%% of the cap receive a counter offer; anything larger is declined.',
            '{"value": 30}'::jsonb, '{"value": 30}'::jsonb,
            'number', '{"min": 0, "max": 1000}'::jsonb, 'high', true
        WHERE NOT EXISTS (
            SELECT 1 FROM bank_rules WHERE rule_key = 'counter_offer_overage_pct'
        )
        """
    )


def downgrade() -> None:
    # Only remove the rows this migration may have INSERTed. The value
    # alignment of foir/income_multiple is intentionally NOT reverted here
    # (the pre-reconciliation values cannot be reliably reconstructed, and the
    # canonical values also match 005's own definition).
    keys = ", ".join(f"'{k}'" for k in _INSERTED_RULE_KEYS)
    op.execute(
        f"DELETE FROM bank_rule_history WHERE rule_id IN "
        f"(SELECT id FROM bank_rules WHERE rule_key IN ({keys}))"
    )
    op.execute(
        f"DELETE FROM user_rule_overrides WHERE rule_id IN "
        f"(SELECT id FROM bank_rules WHERE rule_key IN ({keys}))"
    )
    op.execute(f"DELETE FROM bank_rules WHERE rule_key IN ({keys})")
