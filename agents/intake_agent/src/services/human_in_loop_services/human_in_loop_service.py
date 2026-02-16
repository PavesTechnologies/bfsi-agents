from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from typing import List

from src.repositories.human_in_loop_repo.human_in_loop_repository import HumanInLoopDAO
from src.models.enums import HumanDecision, ApplicantStatus

from src.models.interfaces.human_in_loop_interface import (
    HumanInLoopRequest,
    HumanInLoopResponse,
)
from uuid import UUID
from src.repositories.loan_info.loan_query_dao import LoanQueryDAO


class HumanInLoopService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = HumanInLoopDAO(db)
        self.loan_info_dao = LoanQueryDAO(db)

    async def submit_review(
        self,
        request: HumanInLoopRequest,
    ) -> HumanInLoopResponse:

        try:
            application_id_obj = UUID(request.application_id)
            
            application_info = await self.loan_info_dao.get_loan_by_application_id(application_id_obj)
            
            if not application_info:
                raise HTTPException(
                    status_code=400,
                    detail=f"No loan application found with id {request.application_id}",
                )
                
            if not request.reviewer_id:
                raise HTTPException(
                    status_code=422,
                    detail="Reviewer ID is required",
                )
                
            # -----------------------------
            # 1. Persist human review
            # -----------------------------
            await self.dao.create_review(
                application_id=request.application_id,
                reviewer_id=request.reviewer_id,
                decision=request.decision,
                reason_codes=request.reason_codes,
                comments=request.comments,
            )

            # -----------------------------
            # 2. Decide next application state
            # -----------------------------
            if request.decision == HumanDecision.APPROVE:
                application_status = "APPROVED"
                response_msg = "Application approved. Proceeding to next agent."
            else:
                application_status = "REVISION_REQUIRED"
                response_msg = "Application sent back for revision."

            # -----------------------------
            # 3. Update loan application
            # -----------------------------
            await self.dao.update_application_status(
                application_id=request.application_id,
                status=application_status,
            )   

            # -----------------------------
            
            return HumanInLoopResponse(
                application_id=request.application_id,
                response=response_msg,
            )

        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid application_id format: {request.application_id}",
            )
        
        except SQLAlchemyError:
            await self.db.rollback()
            raise
            
        except HTTPException as e:
            raise e
        
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
