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


class HumanInLoopService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = HumanInLoopDAO(db)

    async def submit_review(
        self,
        request: HumanInLoopRequest,
    ) -> HumanInLoopResponse:

        try:
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

        except SQLAlchemyError:
            await self.db.rollback()
            raise

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
