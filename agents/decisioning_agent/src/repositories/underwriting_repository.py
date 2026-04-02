from sqlalchemy.ext.asyncio import AsyncSession
from src.models.underwriting_decision import UnderwritingDecision
from src.models.underwriting_decision_event import UnderwritingDecisionEvent
from src.services.monitoring.exporter import export_underwriting_decision_metrics
from typing import Dict, Any, Optional
from datetime import datetime

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
        policy_version: Optional[str] = None,
        model_version: Optional[str] = None,
        prompt_version: Optional[str] = None,
        audit_narrative: Optional[Dict[str, Any]] = None,
        raw_state: Optional[Dict[str, Any]] = None,
    ) -> UnderwritingDecision:
        """
        Save underwriting decision to database with complete audit trail.
        
        Handles all three decision types: APPROVE, DECLINE, COUNTER_OFFER
        """
        
        loan_details = final_decision.get("loan_details", {}) if decision == "APPROVE" else {}
        counter_offer_details = counter_offer_data or final_decision.get("counter_offer") or {}
        explanation = (
            loan_details.get("explanation")
            or final_decision.get("original_decision_explanation")
            or final_decision.get("decline_reason")
        )
        decline_reason = final_decision.get("decline_reason") if decision == "DECLINE" else None
        adverse_action_reasons = (
            final_decision.get("adverse_action_reasons")
            if decision == "DECLINE"
            else None
        )
        adverse_action_notice = (
            final_decision.get("adverse_action_notice")
            if decision == "DECLINE"
            else None
        )
        reasoning_summary = (
            final_decision.get("reasoning_summary")
            if decision == "DECLINE"
            else None
        )
        key_factors = (
            final_decision.get("key_factors")
            if decision == "DECLINE"
            else None
        )

        decision_record = UnderwritingDecision(
            application_id=application_id,
            decision=decision,
            risk_tier=aggregated_risk_tier,
            risk_score=aggregated_risk_score,
            
            # --- Loan Details (for APPROVE decisions) ---
            approved_amount=loan_details.get("approved_amount"),
            disbursement_amount=loan_details.get("disbursement_amount"),
            interest_rate=loan_details.get("interest_rate"),
            tenure_months=loan_details.get("approved_tenure_months"),
            
            # --- Decision Details ---
            explanation=explanation,
            decline_reason=decline_reason,
            primary_reason_key=final_decision.get("primary_reason_key"),
            secondary_reason_key=final_decision.get("secondary_reason_key"),
            adverse_action_reasons=adverse_action_reasons,
            adverse_action_notice=adverse_action_notice,
            reasoning_summary=reasoning_summary,
            key_factors=key_factors,
            reasoning_steps=final_decision.get("reasoning_steps"),
            candidate_reason_codes=final_decision.get("candidate_reason_codes"),
            selected_reason_codes=final_decision.get("selected_reason_codes"),
            policy_citations=final_decision.get("policy_citations"),
            retrieval_evidence=final_decision.get("retrieval_evidence"),
            feature_attribution_summary=final_decision.get("feature_attribution_summary"),
            explanation_generation_mode=final_decision.get("explanation_generation_mode"),
            critic_failures=final_decision.get("critic_failures"),
            
            # --- Counter Offer (when applicable) ---
            counter_offer_data=counter_offer_details or None,
            
            # --- Audit & Performance Tracking ---
            thread_id=thread_id,
            execution_time_ms=execution_time_ms,
            parallel_tasks_executed=parallel_tasks_executed,
            node_execution_times=node_execution_times,
            policy_version=policy_version,
            model_version=model_version,
            prompt_version=prompt_version,
            audit_narrative=audit_narrative,
            human_review_required=decision == "REFER_TO_HUMAN",
            human_review_status="PENDING_REVIEW" if decision == "REFER_TO_HUMAN" else None,
            human_review_outcome=None,
            
            # --- Full Audit Trail ---
            raw_decision_payload=raw_state or {"final_decision": final_decision}
        )
        
        self.session.add(decision_record)
        await self.session.commit()
        self.session.add(
            UnderwritingDecisionEvent(
                application_id=application_id,
                underwriting_decision_id=str(decision_record.id) if getattr(decision_record, "id", None) else None,
                event_type="UNDERWRITING_DECISION_CREATED",
                event_status=decision,
                actor="decisioning_agent",
                event_payload={
                    "decision": decision,
                    "policy_version": policy_version,
                    "model_version": model_version,
                    "prompt_version": prompt_version,
                    "policy_citation_count": len(final_decision.get("policy_citations", []) or []),
                    "candidate_reason_count": len(final_decision.get("candidate_reason_codes", []) or []),
                },
            )
        )
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

    async def update_human_review_state(
        self,
        *,
        application_id: str,
        review_status: str,
        review_outcome: str | None,
        latest_human_review_id: str | None,
    ) -> UnderwritingDecision | None:
        decision = await self.get_decision_by_application(application_id)
        if decision is None:
            return None

        decision.human_review_required = True
        decision.human_review_status = review_status
        decision.human_review_outcome = review_outcome
        decision.latest_human_review_id = latest_human_review_id

        existing_audit = decision.audit_narrative or {}
        existing_audit["human_review_required"] = True
        existing_audit["human_review_outcome"] = review_outcome
        decision.audit_narrative = existing_audit

        await self.session.commit()
        self.session.add(
            UnderwritingDecisionEvent(
                application_id=application_id,
                underwriting_decision_id=str(decision.id) if getattr(decision, "id", None) else None,
                event_type="HUMAN_REVIEW_STATE_UPDATED",
                event_status=review_status,
                actor="underwriting_human_review_service",
                event_payload={
                    "review_status": review_status,
                    "review_outcome": review_outcome,
                    "latest_human_review_id": latest_human_review_id,
                },
            )
        )
        await self.session.commit()
        return decision

    def build_monitoring_payload(
        self,
        decision_record: UnderwritingDecision,
        *,
        evaluation_attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Project a persisted decision record into a monitoring-friendly payload."""
        return export_underwriting_decision_metrics(
            decision_record,
            evaluation_attributes=evaluation_attributes,
        )

    async def get_monitoring_payloads(
        self,
        *,
        date_from: datetime,
        date_to: datetime,
        evaluation_attributes: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, Any]]:
        from sqlalchemy import select

        stmt = select(UnderwritingDecision).where(
            UnderwritingDecision.created_at >= date_from,
            UnderwritingDecision.created_at < date_to,
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [
            self.build_monitoring_payload(
                record,
                evaluation_attributes=evaluation_attributes,
            )
            for record in records
        ]
