"""
Disbursement Calculator Service

Calculates EMI, total interest, total repayment,
and generates a full month-by-month amortization schedule.
"""

import math
from datetime import date, timedelta
from typing import List, Dict, Any

from src.domain.entities import EMIInstallment, RepaymentSchedule


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Standard EMI formula:
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    where r = monthly interest rate, n = tenure in months.
    """
    if annual_rate == 0:
        return round(principal / tenure_months, 2)

    monthly_rate = annual_rate / (12 * 100)
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    return round(emi, 2)


def generate_repayment_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    start_date: date | None = None,
) -> RepaymentSchedule:
    """
    Build a full amortization schedule.

    Args:
        principal: Loan principal (approved_amount, not disbursement_amount).
        annual_rate: Annual interest rate as a percentage (e.g. 7.5).
        tenure_months: Repayment tenure in months.
        start_date: Optional first EMI due date. Defaults to 30 days from today.

    Returns:
        A RepaymentSchedule with all installments.
    """
    if start_date is None:
        start_date = date.today() + timedelta(days=30)

    monthly_rate = annual_rate / (12 * 100)
    emi = calculate_emi(principal, annual_rate, tenure_months)

    installments: List[EMIInstallment] = []
    balance = principal
    total_interest = 0.0

    for i in range(1, tenure_months + 1):
        interest_component = round(balance * monthly_rate, 2)
        principal_component = round(emi - interest_component, 2)

        # Handle the last installment rounding
        if i == tenure_months:
            principal_component = round(balance, 2)
            interest_component = round(emi - principal_component, 2) if emi > principal_component else 0.0
            emi_amount = round(principal_component + interest_component, 2)
        else:
            emi_amount = emi

        closing_balance = round(balance - principal_component, 2)
        if closing_balance < 0:
            closing_balance = 0.0

        due_date = start_date + timedelta(days=30 * (i - 1))

        installments.append(
            EMIInstallment(
                installment_number=i,
                due_date=due_date.strftime("%Y-%m-%d"),
                opening_balance=round(balance, 2),
                emi_amount=emi_amount,
                principal_component=principal_component,
                interest_component=interest_component,
                closing_balance=closing_balance,
            )
        )

        total_interest += interest_component
        balance = closing_balance

    total_repayment = round(principal + total_interest, 2)

    return RepaymentSchedule(
        principal=principal,
        annual_interest_rate=annual_rate,
        tenure_months=tenure_months,
        monthly_emi=emi,
        total_interest=round(total_interest, 2),
        total_repayment=total_repayment,
        first_emi_date=start_date.strftime("%Y-%m-%d"),
        installments=installments,
    )
