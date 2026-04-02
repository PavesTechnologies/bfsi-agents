import pytest

from src.domain.decisioning.decision_submission import submit_decline_decision
from src.domain.decisioning.decision_engine import make_underwriting_decision
from src.domain.reason_codes.reason_selector import select_decline_reasons
from src.repositories.underwriting_repository import UnderwritingRepository


def test_select_decline_reasons_prefers_income_and_public_record_triggers():
    result = select_decline_reasons(
        aggregated_risk_tier="F",
        public_record_data={"bankruptcy_present": True, "years_since_bankruptcy": 1, "public_record_severity": "SEVERE"},
        income_data={"income_missing_flag": False, "estimated_dti": 0.52},
        behavior_data={"chargeoff_history": False, "behavior_risk": "FAIR"},
        utilization_data={"utilization_risk": "HIGH"},
        exposure_data={"exposure_risk": "HIGH"},
        inquiry_data={"inquiries_last_12m": 7},
    )

    assert result["primary_reason_key"] == "BANKRUPTCY_RECENT"
    assert result["secondary_reason_key"] == "DTI_HIGH"
    assert len(result["adverse_action_reasons"]) == 2
    assert result["adverse_action_notice"] == "Recent bankruptcy on file; Debt-to-income ratio too high"


def test_submit_decline_decision_rejects_duplicate_or_unknown_reason_keys():
    with pytest.raises(ValueError):
        submit_decline_decision(
            primary_reason_key="DTI_HIGH",
            secondary_reason_key="DTI_HIGH",
            reasoning_summary="duplicate reasons",
        )

    with pytest.raises(ValueError):
        submit_decline_decision(
            primary_reason_key="DTI_HIGH",
            secondary_reason_key="NOT_A_REASON",
            reasoning_summary="unknown reason",
        )


def test_make_underwriting_decision_emits_mapped_decline_reasons():
    result = make_underwriting_decision(
        aggregated_risk_tier="F",
        credit_score_data={"base_limit_band": 5000},
        public_record_data={
            "bankruptcy_present": True,
            "years_since_bankruptcy": 1,
            "public_record_severity": "SEVERE",
            "public_record_adjustment_factor": 0.5,
            "hard_decline_flag": True,
        },
        utilization_data={"utilization_adjustment_factor": 0.7, "utilization_risk": "CRITICAL"},
        inquiry_data={"inquiry_penalty_factor": 0.8, "inquiries_last_12m": 7},
        income_data={"affordability_flag": False, "income_missing_flag": False, "estimated_dti": 0.55},
        behavior_data={"chargeoff_history": False, "behavior_risk": "POOR"},
        exposure_data={"exposure_risk": "HIGH"},
        user_request={"amount": 10000, "tenure": 24},
    )

    assert result.decision == "DECLINE"
    assert result.primary_reason_key == "BANKRUPTCY_RECENT"
    assert result.secondary_reason_key == "DTI_HIGH"
    assert result.adverse_action_reasons is not None
    assert result.adverse_action_reasons[0]["reason_code"] == "PR01"
    assert result.adverse_action_notice is not None
    assert result.reasoning_summary is not None


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.commits += 1

@pytest.mark.anyio
async def test_underwriting_repository_persists_adverse_action_fields():
    session = FakeSession()
    repo = UnderwritingRepository(session)

    await repo.save_decision(
        application_id="APP-999",
        decision="DECLINE",
        final_decision={
            "decision": "DECLINE",
            "decline_reason": "Debt-to-income ratio too high",
            "primary_reason_key": "DTI_HIGH",
            "secondary_reason_key": "EXPOSURE_HIGH",
            "adverse_action_reasons": [
                {"reason_key": "DTI_HIGH", "reason_code": "01", "official_text": "Debt-to-income ratio too high"},
                {"reason_key": "EXPOSURE_HIGH", "reason_code": "EX01", "official_text": "Existing debt obligations are too high"},
            ],
            "adverse_action_notice": "Debt-to-income ratio too high; Existing debt obligations are too high",
            "reasoning_summary": "Deterministic decline reasons selected from triggered policy conditions.",
            "key_factors": [
                "Debt-to-income ratio above policy threshold",
                "High existing debt obligations",
            ],
            "reasoning_steps": ["step 1", "step 2"],
        },
        aggregated_risk_score=10.0,
        aggregated_risk_tier="F",
    )

    saved = session.added[0]
    assert saved.primary_reason_key == "DTI_HIGH"
    assert saved.secondary_reason_key == "EXPOSURE_HIGH"
    assert saved.adverse_action_reasons[0]["reason_code"] == "01"
    assert saved.adverse_action_notice is not None
    assert saved.reasoning_summary is not None
    assert saved.key_factors[0] == "Debt-to-income ratio above policy threshold"
