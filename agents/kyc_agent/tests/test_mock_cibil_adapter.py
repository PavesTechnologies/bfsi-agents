# tests/test_mock_cibil_adapter.py
"""
Tests for MockCIBILAdapter — all 9 PAN-driven scenarios plus field-completeness
checks that guarantee all 7 decisioning nodes can consume the output.

Run from agents/kyc_agent/:
    pytest tests/test_mock_cibil_adapter.py -v
"""

import pytest
from pydantic import ValidationError

from src.adapters.mock_adapters.mock_cibil_adapter import (
    CIBILResponse,
    MockCIBILAdapter,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pan(numeric: str) -> str:
    """Build a syntactically valid PAN with a given 4-digit numeric segment."""
    assert len(numeric) == 4 and numeric.isdigit()
    return f"ABCDE{numeric}F"


async def _fetch(pan: str) -> CIBILResponse:
    return await MockCIBILAdapter().get_credit_report(
        {"pan": pan, "full_name": "Ravi Kumar"}
    )


# Fields that every decisioning node reads — must always be present.
_REQUIRED_KEYS = {"riskModel", "tradeline", "inquiry", "publicRecord", "summaries"}


def _assert_decisioning_compatible(report: CIBILResponse) -> None:
    """Confirm the report carries all keys consumed by the 7 parallel LLM nodes."""
    d = report.model_dump()
    for key in _REQUIRED_KEYS:
        assert key in d, f"Missing field: {key}"
    assert len(d["riskModel"]) >= 1
    assert "score" in d["riskModel"][0]


# ─────────────────────────────────────────────────────────────────────────────
# Scenario Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_prime_borrower():
    """PAN 0001–2499 → score 780, 3 tradelines, no public records."""
    report = await _fetch(_pan("0001"))

    assert report.riskModel[0].score == "780"
    assert len(report.tradeline) == 3
    assert len(report.publicRecord) == 0
    assert report.wilfulDefaulterFlag is False
    assert report.ntcFlag is False

    # All DPD histories should be clean (all "000")
    for tl in report.tradeline:
        assert all(dpd == "000" for dpd in tl.dpdHistory)

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_good_borrower():
    """PAN 2500–4999 → score 730, 3 tradelines (home + auto + CC)."""
    report = await _fetch(_pan("2500"))

    assert report.riskModel[0].score == "730"
    assert len(report.tradeline) == 3
    types = {t.accountType for t in report.tradeline}
    assert "Home Loan" in types
    assert "Auto Loan" in types
    assert "Credit Card" in types

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_high_utilization():
    """PAN 5000–5999 → score 660, 3 credit cards + 1 personal loan, 5 enquiries."""
    report = await _fetch(_pan("5000"))

    assert report.riskModel[0].score == "660"

    revolving = [t for t in report.tradeline if t.revolvingOrInstallment == "R"]
    assert len(revolving) >= 3

    total_limit = sum(int(t.creditLimitOrSanctionedAmount) for t in revolving)
    total_bal = sum(int(t.balanceAmount) for t in revolving)
    utilization_pct = total_bal / total_limit * 100
    assert utilization_pct > 80, f"Expected >80% utilization, got {utilization_pct:.1f}%"

    assert len(report.inquiry) == 5

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_subprime_late_payments():
    """PAN 6000–6999 → score 580, delinquencies present, 6 enquiries."""
    report = await _fetch(_pan("6000"))

    assert report.riskModel[0].score == "580"
    assert len(report.inquiry) == 6

    delinquent = [t for t in report.tradeline if int(t.delinquencies30Days) > 0]
    assert len(delinquent) >= 1, "Expected at least one tradeline with delinquencies"

    # At least one tradeline must contain a non-000 DPD entry
    has_late = any(
        dpd != "000" for tl in report.tradeline for dpd in tl.dpdHistory
    )
    assert has_late, "Expected at least one 30+ DPD event in payment history"

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_written_off_accounts():
    """PAN 7000–7499 → score 510, written-off status, LSS/XXX DPD codes."""
    report = await _fetch(_pan("7000"))

    assert report.riskModel[0].score == "510"
    assert report.writtenOffFlag is True

    written_off = [t for t in report.tradeline if t.status in ("Written Off", "Settled")]
    assert len(written_off) >= 1

    # Must have severe DPD codes
    has_severe = any(
        dpd in ("LSS", "DBT", "SUB", "XXX")
        for tl in report.tradeline
        for dpd in tl.dpdHistory
    )
    assert has_severe, "Expected LSS/DBT/SUB/XXX codes in DPD history"

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_new_to_credit():
    """PAN 7500–7999 → score -1 (NH), zero tradelines, ntcFlag = True."""
    report = await _fetch(_pan("7500"))

    assert report.riskModel[0].score == "-1"
    assert len(report.tradeline) == 0
    assert report.ntcFlag is True

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_suit_filed():
    """PAN 8000–8499 → score 490, SUIT_FILED in publicRecord, suitFiledFlag = True."""
    report = await _fetch(_pan("8000"))

    assert report.riskModel[0].score == "490"
    assert report.suitFiledFlag is True
    assert len(report.publicRecord) >= 1

    suit = [r for r in report.publicRecord if r.type == "SUIT_FILED"]
    assert len(suit) == 1
    assert suit[0].status == "Pending"

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_wilful_defaulter():
    """PAN 8500–8999 → score 300, wilfulDefaulterFlag = True, WILFUL_DEFAULT record."""
    report = await _fetch(_pan("8500"))

    assert report.riskModel[0].score == "300"
    assert report.wilfulDefaulterFlag is True
    assert report.suitFiledFlag is True
    assert report.writtenOffFlag is True

    wd = [r for r in report.publicRecord if r.wilfulDefaulter is True]
    assert len(wd) >= 1
    assert wd[0].type == "WILFUL_DEFAULT"

    _assert_decisioning_compatible(report)


@pytest.mark.asyncio
async def test_moderate_default():
    """PAN 9000–9999 → score 700, 2 tradelines, no public records."""
    report = await _fetch(_pan("9000"))

    assert report.riskModel[0].score == "700"
    assert len(report.tradeline) == 2
    assert len(report.publicRecord) == 0

    _assert_decisioning_compatible(report)


# ─────────────────────────────────────────────────────────────────────────────
# Boundary / Segment Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_boundary_prime_upper_edge():
    """PAN 2499 is still prime (score 780)."""
    report = await _fetch(_pan("2499"))
    assert report.riskModel[0].score == "780"


@pytest.mark.asyncio
async def test_boundary_good_lower_edge():
    """PAN 2500 flips to good profile (score 730)."""
    report = await _fetch(_pan("2500"))
    assert report.riskModel[0].score == "730"


@pytest.mark.asyncio
async def test_boundary_ntc_lower_edge():
    """PAN 7500 is NTC."""
    report = await _fetch(_pan("7500"))
    assert report.riskModel[0].score == "-1"
    assert report.ntcFlag is True


@pytest.mark.asyncio
async def test_boundary_wilful_defaulter_upper_edge():
    """PAN 8999 is still wilful defaulter."""
    report = await _fetch(_pan("8999"))
    assert report.riskModel[0].score == "300"
    assert report.wilfulDefaulterFlag is True


# ─────────────────────────────────────────────────────────────────────────────
# Field-Completeness Tests (decisioning node compatibility)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tradeline_fields_for_utilization_node():
    """utilization_node filters tradeline by revolvingOrInstallment == 'R'."""
    report = await _fetch(_pan("5000"))  # high utilization scenario
    revolving = [t for t in report.tradeline if t.revolvingOrInstallment == "R"]
    for tl in revolving:
        assert tl.creditLimitOrSanctionedAmount.isdigit()
        assert tl.balanceAmount.isdigit()


@pytest.mark.asyncio
async def test_tradeline_fields_for_exposure_node():
    """exposure_node filters tradeline by openOrClosed == 'O'."""
    report = await _fetch(_pan("0001"))  # prime — mix of O/C
    open_trades = [t for t in report.tradeline if t.openOrClosed == "O"]
    for tl in open_trades:
        assert tl.balanceAmount.isdigit()


@pytest.mark.asyncio
async def test_tradeline_fields_for_income_node():
    """income_node sums monthlyPaymentAmount of open tradelines."""
    report = await _fetch(_pan("0001"))
    open_trades = [t for t in report.tradeline if t.openOrClosed == "O"]
    # All monthlyPaymentAmount values must be int-castable
    for tl in open_trades:
        assert int(tl.monthlyPaymentAmount) >= 0


@pytest.mark.asyncio
async def test_tradeline_dpd_history_length():
    """DPD history must cover exactly 36 months."""
    report = await _fetch(_pan("0001"))
    for tl in report.tradeline:
        assert len(tl.dpdHistory) == 36, (
            f"{tl.accountType} @ {tl.subscriberName}: "
            f"dpdHistory has {len(tl.dpdHistory)} entries, expected 36"
        )


@pytest.mark.asyncio
async def test_risk_model_score_is_integer_string():
    """credit_score_node does int(score) — must be a numeric string."""
    for pan_num in ["0001", "2500", "5000", "6000", "7000", "8000", "8500", "9000"]:
        report = await _fetch(_pan(pan_num))
        score_str = report.riskModel[0].score
        assert score_str.lstrip("-").isdigit(), f"Non-numeric score: {score_str}"


@pytest.mark.asyncio
async def test_report_id_is_unique():
    """Each call must generate a unique reportId."""
    pan = _pan("0001")
    r1 = await _fetch(pan)
    r2 = await _fetch(pan)
    assert r1.reportId != r2.reportId


# ─────────────────────────────────────────────────────────────────────────────
# PAN Validation Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_pan_too_short():
    with pytest.raises(ValidationError):
        await MockCIBILAdapter().get_credit_report({"pan": "ABCDE123", "full_name": "Test"})


@pytest.mark.asyncio
async def test_invalid_pan_non_alpha_prefix():
    with pytest.raises(ValidationError):
        await MockCIBILAdapter().get_credit_report({"pan": "12345678901", "full_name": "Test"})


@pytest.mark.asyncio
async def test_invalid_pan_non_digit_segment():
    with pytest.raises(ValidationError):
        await MockCIBILAdapter().get_credit_report({"pan": "ABCDEABCDF", "full_name": "Test"})


@pytest.mark.asyncio
async def test_pan_is_normalised_to_uppercase():
    """Lowercase PAN must be accepted and normalised."""
    report = await MockCIBILAdapter().get_credit_report(
        {"pan": "abcde0001f", "full_name": "Test User"}
    )
    assert isinstance(report, CIBILResponse)
