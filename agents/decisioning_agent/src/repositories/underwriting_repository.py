from sqlalchemy.ext.asyncio import AsyncSession
from src.models.underwriting_decision import UnderwritingDecision
from src.core.database import get_db

class UnderwritingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_decision(self, decision_data: dict):
        decision = UnderwritingDecision(
            application_id=decision_data.get("application_id"),
            correlation_id=decision_data.get("correlation_id"),
            decision=decision_data.get("decision"),
            risk_tier=decision_data.get("risk_tier"),
            risk_score=decision_data.get("risk_score"),
            approved_amount=decision_data.get("loan_details", {}).get("approved_amount") if decision_data.get("loan_details") else None,
            interest_rate=decision_data.get("loan_details", {}).get("interest_rate") if decision_data.get("loan_details") else None,
            tenure_months=decision_data.get("loan_details", {}).get("approved_tenure_months") if decision_data.get("loan_details") else None,
            explanation=decision_data.get("explanation") or decision_data.get("loan_details", {}).get("explanation") or decision_data.get("decline_reason"),
            reasoning_steps=decision_data.get("reasoning_steps"),
            raw_decision_payload=decision_data
        )
        self.session.add(decision)
        await self.session.commit()
        return decision
