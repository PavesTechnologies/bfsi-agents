"""
Demo Script for Disbursement Agent

This script demonstrates the Disbursement Agent's workflow directly
by calling the orchestrator with mock decision payloads.
"""

import json
from src.services.orchestrator import run_disbursement
from src.domain.entities import DisbursementRequest


def run_demo():
    print("=" * 60)
    print("Disbursement Agent Demo")
    print("=" * 60)

    # --- 1. APPROVE Flow Demo ---
    print("\n[SCENARIO 1] Processing an APPROVED Loan")
    approve_request = DisbursementRequest(
        application_id="APP_001",
        decision="APPROVE",
        risk_tier="B",
        risk_score=75.5,
        loan_details={
            "approved_amount": 100000.0,
            "approved_tenure_months": 36,
            "interest_rate": 9.5,
            "disbursement_amount": 98000.0,
            "explanation": "High credit score and stable income."
        }
    )

    receipt_approve = run_disbursement(approve_request)
    print(f"Status: {receipt_approve['disbursement_status']}")
    print(f"Transaction ID: {receipt_approve['transaction_id']}")
    print(f"Monthly EMI: ${receipt_approve['monthly_emi']}")
    print(f"Schedule Preview (First Installment): {receipt_approve['schedule_preview'][0]}")

    # --- 2. COUNTER_OFFER Flow Demo ---
    print("\n[SCENARIO 2] Processing an accepted COUNTER_OFFER")
    counter_offer_request = DisbursementRequest(
        application_id="APP_002",
        decision="COUNTER_OFFER",
        counter_offer={
            "generated_options": [
                {
                    "option_id": "OPT_LOWER_AMT",
                    "proposed_amount": 35000.0,
                    "proposed_tenure_months": 24,
                    "proposed_interest_rate": 10.5,
                    "disbursement_amount": 34300.0,
                    "monthly_payment_emi": 1622.5,
                    "total_repayment": 38940.0
                }
            ]
        },
        selected_option_id="OPT_LOWER_AMT"
    )

    receipt_counter = run_disbursement(counter_offer_request)
    print(f"Status: {receipt_counter['disbursement_status']}")
    print(f"Transaction ID: {receipt_counter['transaction_id']}")
    print(f"Monthly EMI: ${receipt_counter['monthly_emi']}")
    print(f"Approved Amount: ${receipt_counter['approved_amount']}")

    # --- 3. DECLINE Flow Demo (Failure Case) ---
    print("\n[SCENARIO 3] Handling a DECLINED Loan")
    decline_request = DisbursementRequest(
        application_id="APP_003",
        decision="DECLINE",
        decline_reason="Insufficient income for requested amount."
    )

    receipt_decline = run_disbursement(decline_request)
    print(f"Status: {receipt_decline['disbursement_status']}")
    print(f"Explanation: {receipt_decline['explanation']}")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
