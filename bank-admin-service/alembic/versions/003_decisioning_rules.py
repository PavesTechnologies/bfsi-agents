"""decisioning rules - bands, factors, and orchestration values

Revision ID: 003_decisioning_rules
Revises: 002_hitl_and_user_rules
Create Date: 2026-05-08
"""
from typing import Sequence, Union
from alembic import op


revision: str = "003_decisioning_rules"
down_revision: Union[str, Sequence[str], None] = "002_hitl_and_user_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Rule keys seeded by this migration. Tracked here so downgrade() can remove
# exactly the rows it inserted without disturbing rows seeded elsewhere.
_NEW_RULE_KEYS: tuple[str, ...] = (
    "score_bands",
    "severity_bands",
    "bankruptcy_hard_decline_years",
    "utilization_bands",
    "monthly_obligation_bands",
    "emi_estimation_pct_of_balance",
    "delinquency_bands",
    "chargeoff_dpd_codes",
    "chargeoff_hard_decline",
    "inquiry_velocity_bands",
    "dti_bands",
    "tier_thresholds",
    "tier_interest_rates",
    "risk_weights",
    "risk_flag_score_map",
)


def upgrade() -> None:
    # 1) New 'decision' rule category for orchestration values that the
    #    risk_aggregator and decision_llm nodes read at runtime.
    op.execute(
        "INSERT INTO rule_categories (name, description) VALUES "
        "('decision', 'Risk aggregation tier thresholds, weights, pricing, and risk-flag normalization')"
    )

    # 2) Seed all rules required by the analyzer + orchestration nodes that
    #    aren't covered by 001_initial_schema. JSON literals use $tag$...$tag$
    #    quoting so we don't have to double single quotes.
    op.execute(
        r"""
        INSERT INTO bank_rules (
            category_id, rule_key, display_name, description,
            current_value, default_value, data_type, validation_schema,
            risk_level, requires_approval
        ) VALUES
        -- credit_score ---------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'credit_score'),
            'score_bands',
            'CIBIL Score Bands',
            'Score band definitions with min/max range, base lending limit (INR), risk flag, and aggregation weight.',
            $j$ {"value": [
                {"label": "PRIME",      "min": 750, "max": 900, "base_limit": 75000, "risk_flag": "LOW",      "weight": 0.25},
                {"label": "NEAR_PRIME", "min": 700, "max": 749, "base_limit": 50000, "risk_flag": "MODERATE", "weight": 0.25},
                {"label": "FAIR",       "min": 650, "max": 699, "base_limit": 35000, "risk_flag": "HIGH",     "weight": 0.25},
                {"label": "SUBPRIME",   "min": 600, "max": 649, "base_limit": 20000, "risk_flag": "HIGH",     "weight": 0.25}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "PRIME",      "min": 750, "max": 900, "base_limit": 75000, "risk_flag": "LOW",      "weight": 0.25},
                {"label": "NEAR_PRIME", "min": 700, "max": 749, "base_limit": 50000, "risk_flag": "MODERATE", "weight": 0.25},
                {"label": "FAIR",       "min": 650, "max": 699, "base_limit": 35000, "risk_flag": "HIGH",     "weight": 0.25},
                {"label": "SUBPRIME",   "min": 600, "max": 649, "base_limit": 20000, "risk_flag": "HIGH",     "weight": 0.25}
            ]} $j$::jsonb,
            'json', NULL, 'high', true
        ),

        -- public_record --------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'public_record'),
            'severity_bands',
            'Public Record Severity Bands',
            'Severity classification with adjustment factor multiplied into the max approved amount.',
            $j$ {"value": [
                {"label": "NONE",     "adjustment_factor": 1.00},
                {"label": "LOW",      "adjustment_factor": 0.90},
                {"label": "MODERATE", "adjustment_factor": 0.75},
                {"label": "SEVERE",   "adjustment_factor": 0.50}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "NONE",     "adjustment_factor": 1.00},
                {"label": "LOW",      "adjustment_factor": 0.90},
                {"label": "MODERATE", "adjustment_factor": 0.75},
                {"label": "SEVERE",   "adjustment_factor": 0.50}
            ]} $j$::jsonb,
            'json', NULL, 'high', true
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'public_record'),
            'bankruptcy_hard_decline_years',
            'Bankruptcy Hard-Decline Window (years)',
            'If a bankruptcy was filed within this many years, hard-decline the application.',
            '{"value": 2}'::jsonb, '{"value": 2}'::jsonb,
            'number', '{"min": 0, "max": 20}'::jsonb, 'low', false
        ),

        -- utilization ----------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'utilization'),
            'utilization_bands',
            'Revolving Utilization Bands',
            'Utilization ratio bands (0-1) with adjustment factor multiplied into the max approved amount.',
            $j$ {"value": [
                {"label": "EXCELLENT", "min": 0.00, "max": 0.15, "adjustment_factor": 1.10},
                {"label": "GOOD",      "min": 0.16, "max": 0.35, "adjustment_factor": 1.00},
                {"label": "HIGH",      "min": 0.36, "max": 0.60, "adjustment_factor": 0.85},
                {"label": "CRITICAL",  "min": 0.61, "max": 1.00, "adjustment_factor": 0.70}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "EXCELLENT", "min": 0.00, "max": 0.15, "adjustment_factor": 1.10},
                {"label": "GOOD",      "min": 0.16, "max": 0.35, "adjustment_factor": 1.00},
                {"label": "HIGH",      "min": 0.36, "max": 0.60, "adjustment_factor": 0.85},
                {"label": "CRITICAL",  "min": 0.61, "max": 1.00, "adjustment_factor": 0.70}
            ]} $j$::jsonb,
            'json', NULL, 'low', false
        ),

        -- exposure -------------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'exposure'),
            'monthly_obligation_bands',
            'Monthly Obligation Bands (INR)',
            'Monthly debt-payment thresholds for exposure classification. max=null means unbounded upper.',
            $j$ {"value": [
                {"label": "LOW",      "min": 0,    "max": 500},
                {"label": "MODERATE", "min": 500,  "max": 1500},
                {"label": "HIGH",     "min": 1500, "max": 3500},
                {"label": "EXTREME",  "min": 3500, "max": null}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "LOW",      "min": 0,    "max": 500},
                {"label": "MODERATE", "min": 500,  "max": 1500},
                {"label": "HIGH",     "min": 1500, "max": 3500},
                {"label": "EXTREME",  "min": 3500, "max": null}
            ]} $j$::jsonb,
            'json', NULL, 'low', false
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'exposure'),
            'emi_estimation_pct_of_balance',
            'EMI Estimation %% of Balance',
            'When a tradeline lacks monthly_payment, estimate EMI as this percent of outstanding balance.',
            '{"value": 0.05}'::jsonb, '{"value": 0.05}'::jsonb,
            'number', '{"min": 0.005, "max": 0.5}'::jsonb, 'low', false
        ),

        -- behavior -------------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'behavior'),
            'delinquency_bands',
            'Delinquency Bands',
            'Delinquency-count thresholds mapping to behavior_score and behavior_risk. max_count=null means unbounded.',
            $j$ {"value": [
                {"label": "EXCELLENT",    "max_count": 0,    "behavior_score": 100, "behavior_risk": "LOW"},
                {"label": "FAIR",         "max_count": 2,    "behavior_score": 75,  "behavior_risk": "MODERATE"},
                {"label": "POOR",         "max_count": 4,    "behavior_score": 40,  "behavior_risk": "HIGH"},
                {"label": "UNACCEPTABLE", "max_count": null, "behavior_score": 0,   "behavior_risk": "HIGH"}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "EXCELLENT",    "max_count": 0,    "behavior_score": 100, "behavior_risk": "LOW"},
                {"label": "FAIR",         "max_count": 2,    "behavior_score": 75,  "behavior_risk": "MODERATE"},
                {"label": "POOR",         "max_count": 4,    "behavior_score": 40,  "behavior_risk": "HIGH"},
                {"label": "UNACCEPTABLE", "max_count": null, "behavior_score": 0,   "behavior_risk": "HIGH"}
            ]} $j$::jsonb,
            'json', NULL, 'low', false
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'behavior'),
            'chargeoff_dpd_codes',
            'Charge-off DPD Codes',
            'DPD-history codes that indicate a charge-off / loss / sub-standard event.',
            $j$ {"value": ["SUB", "DBT", "LSS", "XXX", "060", "090", "120", "150", "180"]} $j$::jsonb,
            $j$ {"value": ["SUB", "DBT", "LSS", "XXX", "060", "090", "120", "150", "180"]} $j$::jsonb,
            'json', NULL, 'low', false
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'behavior'),
            'chargeoff_hard_decline',
            'Charge-off Hard Decline',
            'When true, presence of any charge-off code triggers a hard decline.',
            '{"value": true}'::jsonb, '{"value": true}'::jsonb,
            'boolean', NULL, 'high', true
        ),

        -- inquiry --------------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'inquiry'),
            'inquiry_velocity_bands',
            'Inquiry Velocity Bands (12m)',
            'Recent-inquiry count thresholds (12-month window) and the penalty factor multiplier per band.',
            $j$ {"value": [
                {"label": "LOW",      "max_inquiries_12m": 2,    "penalty_factor": 1.00},
                {"label": "MODERATE", "max_inquiries_12m": 4,    "penalty_factor": 0.95},
                {"label": "HIGH",     "max_inquiries_12m": null, "penalty_factor": 0.85}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "LOW",      "max_inquiries_12m": 2,    "penalty_factor": 1.00},
                {"label": "MODERATE", "max_inquiries_12m": 4,    "penalty_factor": 0.95},
                {"label": "HIGH",     "max_inquiries_12m": null, "penalty_factor": 0.85}
            ]} $j$::jsonb,
            'json', NULL, 'low', false
        ),

        -- income ---------------------------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'income'),
            'dti_bands',
            'DTI Bands',
            'DTI ratio bands (0-1) with associated income_risk classification.',
            $j$ {"value": [
                {"label": "LOW",          "min": 0.00, "max": 0.30, "income_risk": "LOW"},
                {"label": "MODERATE",     "min": 0.30, "max": 0.45, "income_risk": "MODERATE"},
                {"label": "HIGH",         "min": 0.45, "max": 0.50, "income_risk": "HIGH"},
                {"label": "UNACCEPTABLE", "min": 0.50, "max": 1.00, "income_risk": "HIGH"}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"label": "LOW",          "min": 0.00, "max": 0.30, "income_risk": "LOW"},
                {"label": "MODERATE",     "min": 0.30, "max": 0.45, "income_risk": "MODERATE"},
                {"label": "HIGH",         "min": 0.45, "max": 0.50, "income_risk": "HIGH"},
                {"label": "UNACCEPTABLE", "min": 0.50, "max": 1.00, "income_risk": "HIGH"}
            ]} $j$::jsonb,
            'json', NULL, 'low', false
        ),

        -- decision (orchestration) ---------------------------------------
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'tier_thresholds',
            'Risk Tier Thresholds',
            'Aggregated risk-score thresholds (0-100) defining tier boundaries A/B/C/D/F.',
            $j$ {"value": [
                {"tier": "A", "min": 80},
                {"tier": "B", "min": 65},
                {"tier": "C", "min": 50},
                {"tier": "D", "min": 35},
                {"tier": "F", "min": 0}
            ]} $j$::jsonb,
            $j$ {"value": [
                {"tier": "A", "min": 80},
                {"tier": "B", "min": 65},
                {"tier": "C", "min": 50},
                {"tier": "D", "min": 35},
                {"tier": "F", "min": 0}
            ]} $j$::jsonb,
            'json', NULL, 'high', true
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'tier_interest_rates',
            'Tier Interest Rates (%% APR)',
            'Annual interest rate (percent) applied per tier. F is 0 (no rate applies on declines).',
            $j$ {"value": {"A": 9.5, "B": 12.0, "C": 15.5, "D": 20.0, "F": 0.0}} $j$::jsonb,
            $j$ {"value": {"A": 9.5, "B": 12.0, "C": 15.5, "D": 20.0, "F": 0.0}} $j$::jsonb,
            'json', NULL, 'high', true
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'risk_weights',
            'Aggregator Risk Weights',
            'Per-analyzer weight in the aggregated risk score. Must sum to 1.0.',
            $j$ {"value": {
                "credit_score":  0.25,
                "public_record": 0.15,
                "utilization":   0.15,
                "exposure":      0.10,
                "behavior":      0.15,
                "inquiry":       0.05,
                "income":        0.15
            }} $j$::jsonb,
            $j$ {"value": {
                "credit_score":  0.25,
                "public_record": 0.15,
                "utilization":   0.15,
                "exposure":      0.10,
                "behavior":      0.15,
                "inquiry":       0.05,
                "income":        0.15
            }} $j$::jsonb,
            'json', NULL, 'high', true
        ),
        (
            (SELECT id FROM rule_categories WHERE name = 'decision'),
            'risk_flag_score_map',
            'Risk Flag → 0-100 Score Map',
            'Mapping from text risk flags emitted by analyzer LLMs to numeric sub-scores.',
            $j$ {"value": {
                "LOW": 90, "MODERATE": 60, "HIGH": 30,
                "EXCELLENT": 95, "GOOD": 75, "CRITICAL": 10,
                "EXTREME": 5,
                "FAIR": 65, "POOR": 30, "UNACCEPTABLE": 5,
                "NONE": 100, "SEVERE": 10
            }} $j$::jsonb,
            $j$ {"value": {
                "LOW": 90, "MODERATE": 60, "HIGH": 30,
                "EXCELLENT": 95, "GOOD": 75, "CRITICAL": 10,
                "EXTREME": 5,
                "FAIR": 65, "POOR": 30, "UNACCEPTABLE": 5,
                "NONE": 100, "SEVERE": 10
            }} $j$::jsonb,
            'json', NULL, 'low', false
        )
        """
    )

    # 3) Re-categorize 'origination_fee_pct' from 'income' to 'decision'.
    #    It's a pricing knob the decision_llm node reads — belongs with the
    #    other decision-orchestration rules (tier_interest_rates, weights).
    op.execute(
        "UPDATE bank_rules "
        "SET category_id = (SELECT id FROM rule_categories WHERE name = 'decision') "
        "WHERE rule_key = 'origination_fee_pct'"
    )


def downgrade() -> None:
    # Move 'origination_fee_pct' back to its original 'income' category before
    # dropping the 'decision' category (FK would otherwise complain).
    op.execute(
        "UPDATE bank_rules "
        "SET category_id = (SELECT id FROM rule_categories WHERE name = 'income') "
        "WHERE rule_key = 'origination_fee_pct'"
    )

    # Remove only the rows this migration inserted, then the new category.
    keys = ", ".join(f"'{k}'" for k in _NEW_RULE_KEYS)
    op.execute(f"DELETE FROM bank_rule_history WHERE rule_id IN (SELECT id FROM bank_rules WHERE rule_key IN ({keys}))")
    op.execute(f"DELETE FROM user_rule_overrides WHERE rule_id IN (SELECT id FROM bank_rules WHERE rule_key IN ({keys}))")
    op.execute(f"DELETE FROM bank_rules WHERE rule_key IN ({keys})")
    op.execute("DELETE FROM rule_categories WHERE name = 'decision'")
