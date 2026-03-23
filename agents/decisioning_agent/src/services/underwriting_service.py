"""
Underwriting Service

Entry point for running the decisioning workflow.
Accepts an UnderwritingRequest and returns the final decision payload.
"""


import uuid
import time

from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.underwriting_models import UnderwritingRequest
from src.repositories.langgraph_failed_th_repository import (
    DecisioningFailedThreadRepository,
)
from src.repositories.underwriting_repository import UnderwritingRepository
from src.workflows.decision_flow import build_underwriting_graph
from fastapi import HTTPException

class UnderwritingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.failed_thread_repo = DecisioningFailedThreadRepository(db)
        self.underwriting_repo = UnderwritingRepository(db)
        self.graph = build_underwriting_graph()

    async def execute_underwriting(self, request: UnderwritingRequest) -> dict:
        """
        Execute underwriting workflow and save decision to database.
        
        Handles:
        - APPROVE: Complete loan offer with terms
        - DECLINE: Rejection with reasoning
        - COUNTER_OFFER: Alternative loan terms
        """
        
        failed_app = await self.failed_thread_repo.get_failed_thread(request.application_id)
        
        if failed_app:
            thread_id = failed_app.thread_id
            print("Resuming failed thread:", thread_id)
        else:
            print("New workflow for application:", request.application_id)
            thread_id = f"underwriting_{request.application_id}"
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            start_time = time.time()
            
            initial_state = {
                    "application_id": request.application_id,
                    "raw_experian_data": request.raw_experian_data,
                    "user_request": {
                        "amount": request.requested_amount,
                        "tenure": request.requested_tenure_months,
                    },
                    "bank_statement_summary": {
                        "monthly_income": request.monthly_income,
                    },
                }

            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            response_payload = final_state.get("final_decision", {})

            if not response_payload:
                raise HTTPException(
                    status_code=500,
                    detail="Graph execution completed but no final response payload was produced.",
                )

            # Extract decision and related data from final state
            decision = response_payload.get("decision", "UNKNOWN")
            counter_offer_data = None
            
            if decision == "COUNTER_OFFER":
                counter_offer_data = final_state.get("counter_offer_data", {})
                response_payload["counter_offer_data"] = counter_offer_data
            
            # ✅ Save decision to database with complete audit trail
            await self.underwriting_repo.save_decision(
                application_id=request.application_id,
                decision=decision,
                final_decision=response_payload,
                aggregated_risk_score=final_state.get("aggregated_risk_score"),
                aggregated_risk_tier=final_state.get("aggregated_risk_tier"),
                counter_offer_data=counter_offer_data,
                thread_id=thread_id,
                execution_time_ms=execution_time_ms,
                parallel_tasks_executed=final_state.get("parallel_tasks_completed", []),
                node_execution_times=final_state.get("node_execution_times", {}),
                raw_state=final_state,
            )
            
            await self.failed_thread_repo.delete_failed_thread(request.application_id)
            return response_payload

        except HTTPException as e:
            await self.failed_thread_repo.save_failure(
                application_id=request.application_id,
                thread_id=thread_id,
                error_message=str(e.detail),
            )
            raise
        except Exception as e:
            await self.failed_thread_repo.save_failure(
                application_id=request.application_id,
                thread_id=thread_id,
                error_message=str(e),
            )
            raise HTTPException(status_code=500, detail=str(e))
