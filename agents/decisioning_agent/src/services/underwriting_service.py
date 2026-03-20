"""
Underwriting Service

Entry point for running the decisioning workflow.
Accepts an UnderwritingRequest and returns the final decision payload.
"""


import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.underwriting_models import UnderwritingRequest
from src.repositories.langgraph_failed_th_repository import (
    DecisioningFailedThreadRepository,
)
from src.workflows.decision_flow import build_underwriting_graph
from fastapi import HTTPException

# _graph = build_underwriting_graph()


# async def _execute_underwriting(request: UnderwritingRequest) -> dict:
#     request_payload = request.model_dump(mode="json")
#     request_hash = stable_payload_hash(request_payload)
#     initial_state = {
#                 "application_id": request.application_id,
#                 # "correlation_id": correlation_id,
#                 "raw_experian_data": request.raw_experian_data,
#                 "user_request": {
#                     "amount": request.requested_amount,
#                     "tenure": request.requested_tenure_months,
#                 },
#                 "bank_statement_summary": {
#                     "monthly_income": request.monthly_income,
#                 },
#             }

#     final_state = await _graph.ainvoke(initial_state)
#     response_payload = final_state.get("final_response_payload", {})
#     return response_payload

# def run_underwriting(request: UnderwritingRequest) -> dict:
#     """
#     Execute the underwriting decision workflow.

#     Args:
#         request: An UnderwritingRequest containing applicant, credit,
#                  and financial data for risk evaluation.

#     Returns:
#         The final decision response payload as a dict.
#     """

#     result = _execute_underwriting(request)
#     print("Graph execution result Underwriting:", result)
#     return result


class UnderwritingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.failed_thread_repo = DecisioningFailedThreadRepository(db)
        self.graph = build_underwriting_graph()

    async def execute_underwriting(self, request: UnderwritingRequest) -> dict:
        
        failed_app = await self.failed_thread_repo.get_failed_thread(request.application_id)
        
        if failed_app:
            thread_id = failed_app.thread_id
            print("Resuming failed thread:", thread_id)
        else:
            print("New workflow for application:", request.application_id)
            thread_id = f"underwriting_{request.application_id}"
        
        config = {"configurable": {"thread_id": thread_id}}
        try:
            initial_state = {
                    "application_id": request.application_id,
                    # "correlation_id": correlation_id,
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
            response_payload = final_state.get(
                "final_decision", {}
            )

            if not response_payload:
                raise HTTPException(
                    status_code=500,
                    detail="Graph execution completed but no final response payload was produced.",
                )

            if (response_payload.get("decision") == "COUNTER_OFFER"):
                
                response_payload["counter_offer_data"] = final_state.get("counter_offer_data", {})

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
