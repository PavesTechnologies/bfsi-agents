from src.domain.calculators.credit_banding import classify_credit_score
from src.domain.calculators.public_records import classify_public_records
from src.policy.policy_loader import load_policy_config


def test_policy_loader_reads_bank_risk_config():
    policy = load_policy_config()

    assert policy["bank"]["policy_version"] == "v2.0"
    assert "credit_score" in policy
    assert "public_records" in policy


def test_credit_score_classification_uses_configured_band_thresholds():
    result = classify_credit_score(710, load_policy_config())

    assert result["score_band"] == "NEAR_PRIME"
    assert result["base_limit_band"] == 60000.0
    assert result["score_risk_flag"] == "MODERATE"


def test_credit_score_classification_handles_prime_boundary():
    result = classify_credit_score(760, load_policy_config())

    assert result["score_band"] == "PRIME"
    assert result["base_limit_band"] == 100000.0
    assert result["score_risk_flag"] == "LOW"


def test_public_record_classification_sets_hard_decline_for_recent_bankruptcy():
    records = [{"filingDate": "01012025", "status": "15"}]

    result = classify_public_records(records, load_policy_config())

    assert result["bankruptcy_present"] is True
    assert result["public_record_severity"] == "SEVERE"
    assert result["hard_decline_flag"] is True


def test_public_record_classification_sets_moderate_for_older_bankruptcy():
    records = [{"filingDate": "09022019", "status": "15"}]

    result = classify_public_records(records, load_policy_config())

    assert result["bankruptcy_present"] is True
    assert result["years_since_bankruptcy"] >= 5
    assert result["public_record_severity"] == "MODERATE"
    assert result["public_record_adjustment_factor"] == 0.75
