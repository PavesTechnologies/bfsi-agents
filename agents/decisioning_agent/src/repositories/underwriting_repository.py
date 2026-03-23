from sqlalchemy.ext.asyncio import AsyncSession
from src.models.underwriting_decision import UnderwritingDecision
from src.core.database import get_db
from typing import Dict, Any, Optional

class UnderwritingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_decision(
        self, 
        application_id: str,
        decision: str,  # "APPROVE", "DECLINE", "COUNTER_OFFER"
        final_decision: Dict[str, Any],
        aggregated_risk_score: Optional[float] = None,
        aggregated_risk_tier: Optional[str] = None,
        counter_offer_data: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        parallel_tasks_executed: Optional[list] = None,
        node_execution_times: Optional[Dict[str, float]] = None,
        raw_state: Optional[Dict[str, Any]] = None,
    ) -> UnderwritingDecision:
        """
        Save underwriting decision to database with complete audit trail.
        
        Handles all three decision types: APPROVE, DECLINE, COUNTER_OFFER
        """
        
        decision_record = UnderwritingDecision(
            application_id=application_id,
            decision=decision,
            risk_tier=aggregated_risk_tier,
            risk_score=aggregated_risk_score,
            
            # --- Loan Details (for APPROVE decisions) ---
            approved_amount=final_decision.get("approved_amount"),
            disbursement_amount=final_decision.get("disbursement_amount"),
            interest_rate=final_decision.get("interest_rate"),
            tenure_months=final_decision.get("approved_tenure"),
            
            # --- Decision Details ---
            explanation=final_decision.get("explanation"),
            decline_reason=final_decision.get("explanation") if decision == "DECLINE" else None,
            reasoning_steps=final_decision.get("reasoning_steps"),
            
            # --- Counter Offer (when applicable) ---
            counter_offer_data=counter_offer_data,
            
            # --- Audit & Performance Tracking ---
            thread_id=thread_id,
            execution_time_ms=execution_time_ms,
            parallel_tasks_executed=parallel_tasks_executed,
            node_execution_times=node_execution_times,
            
            # --- Full Audit Trail ---
            raw_decision_payload=raw_state or {"final_decision": final_decision}
        )
        
        self.session.add(decision_record)
        await self.session.commit()
        return decision_record
    
    async def get_decision_by_application(self, application_id: str) -> Optional[UnderwritingDecision]:
        """Retrieve decision history for an application."""
        from sqlalchemy import select
        stmt = select(UnderwritingDecision).where(
            UnderwritingDecision.application_id == application_id
        ).order_by(UnderwritingDecision.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all_decisions_for_application(self, application_id: str) -> list[UnderwritingDecision]:
        """Retrieve all decisions for an application (audit history)."""
        from sqlalchemy import select
        stmt = select(UnderwritingDecision).where(
            UnderwritingDecision.application_id == application_id
        ).order_by(UnderwritingDecision.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
