"""income-based eligibility rules - tier FOIR, income multiple cap, affordability floor, counter-offer overage

Revision ID: 005_income_based_eligibility
Revises: 004_counter_offer_session
Create Date: 2026-06-03

Seeds four NEW rules into the existing 'decision' category. These drive the
income-driven affordability rewrite of the decision engine:

  foir_threshold_by_tier      - max %% of gross monthly income toward all EMIs, per tier
  income_multiple_cap_by_tier - hard ceiling as a multiple of annual income, per tier
  min_disposable_income_pct   - affordability floor so max affordable EMI is never 0
  counter_offer_overage_pct   - reject (instead of counter-offer) when the requested
                                amount exceeds the qualifying cap by more than this %%

No existing rows are modified. score_bands keeps its base_limit field (now unused by
the decision node) so this migration stays additive and low-risk.
"""
from typing import Sequence, Union
from alembic import op


revision: str = "005_income_based_eligibility"
down_revision: Union[str, Sequence[str], None] = "004_counter_offer_session"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Rule keys seeded by this migration. Tracked so downgrade() removes exactly the
# rows it inserted, without disturbing rows seeded elsewhere.
_NEW_RULE_KEYS: tuple[str, ...] = (
    "foir_threshold_by_tier",
    "income_multiple_cap_by_tier",
    "min_disposable_income_pct",
    "counter_offer_overage_pct",
)


def upgrade() -> None:
    # All four rules live in the 'decision' category created by
    # 003_decisioning_rules. JSON literals use $j$...$j$ quoting; literal
    # percent signs in display_name/description are doubled (%%) so the
    # DBAPI paramstyle layer does not treat them as format placeholders.
    op.execute(
        r"""
        INSERT INTO bank_rules (
            category_id, rule_key, display_name, description,
            current_value, default_value, data_type, validation_schema,
            risk_level, requires_approval
        ) VALUES
        -- FOIR threshold per tier ----------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'foir_threshold_by_tier',
            'FOIR Threshold by Risk Tier (%%)',
            'Maximum percent of gross monthly income that may go toward all EMIs (existing obligations + the new loan), per risk tier. Higher tiers get more headroom. Drives the max affordable EMI and the income-based loan cap.',
            $j$ {"value": {"A": 60, "B": 55, "C": 50, "D": 45, "F": 40}} $j$::jsonb,
            $j$ {"value": {"A": 60, "B": 55, "C": 50, "D": 45, "F": 40}} $j$::jsonb,
            'json', NULL, 'high', true
        ),

        -- Income multiple ceiling per tier -------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'income_multiple_cap_by_tier',
            'Max Loan as Multiple of Annual Income (by Tier)',
            'Hard ceiling on the approved loan as a multiple of annual income (monthly income x 12 x multiple), per tier. Prevents very-long-tenure loans that are disproportionate to the applicant''s total earning capacity. 0 means no income-multiple lending for that tier.',
            $j$ {"value": {"A": 24, "B": 20, "C": 15, "D": 10, "F": 0}} $j$::jsonb,
            $j$ {"value": {"A": 24, "B": 20, "C": 15, "D": 10, "F": 0}} $j$::jsonb,
            'json', NULL, 'high', true
        ),

        -- Affordability floor --------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'min_disposable_income_pct',
            'Minimum Disposable Income Floor (%% of Income)',
            'Affordability floor. The max affordable EMI never drops below this percent of gross monthly income, even when existing obligations are high. Guarantees affordability is never zero for an applicant who has income.',
            '{"value": 10}'::jsonb, '{"value": 10}'::jsonb,
            'number', '{"min": 0, "max": 100}'::jsonb, 'high', true
        ),

        -- Counter-offer overage limit ------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'counter_offer_overage_pct',
            'Counter-Offer Overage Limit (%% over cap)',
            'If the requested amount exceeds the max approvable amount by more than this percent, the application is declined instead of generating a counter offer. Example: 30 means requests up to 130%% of the cap receive a counter offer; anything larger is declined.',
            '{"value": 30}'::jsonb, '{"value": 30}'::jsonb,
            'number', '{"min": 0, "max": 1000}'::jsonb, 'high', true
        )
        """
    )


def downgrade() -> None:
    # Remove only the rows this migration inserted. The 'decision' category
    # itself is owned by 003_decisioning_rules and is left intact.
    keys = ", ".join(f"'{k}'" for k in _NEW_RULE_KEYS)
    op.execute(
        f"DELETE FROM bank_rule_history WHERE rule_id IN "
        f"(SELECT id FROM bank_rules WHERE rule_key IN ({keys}))"
    )
    op.execute(
        f"DELETE FROM user_rule_overrides WHERE rule_id IN "
        f"(SELECT id FROM bank_rules WHERE rule_key IN ({keys}))"
    )
    op.execute(f"DELETE FROM bank_rules WHERE rule_key IN ({keys})")
