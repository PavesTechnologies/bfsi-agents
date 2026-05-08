import uuid
import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.loan_application import LoanApplication, PipelineStatus
from src.schemas.loan_application import (
    LoanApplicationCreate,
    AnalyzerSelectionRequest,
    BankDecisionRequest,
    DecisioningResultPatch,
    SignaturePatch,
    DisbursementPatch,
    LoanApplicationListResponse,
    LoanApplicationSummary,
)

_NOT_FOUND = status.HTTP_404_NOT_FOUND


class LoanApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── private helpers ─────────────────────────────────────────────────────

    async def _get_one(self, filter_col, value) -> LoanApplication:
        result = await self.db.execute(select(LoanApplication).where(filter_col == value))
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=_NOT_FOUND, detail=f"Application not found: {value}")
        return app

    def _now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    # ── public interface ─────────────────────────────────────────────────────

    async def create(self, payload: LoanApplicationCreate) -> LoanApplication:
        now = self._now()
        app = LoanApplication(
            external_application_id=payload.external_application_id,
            pipeline_status=PipelineStatus.AWAITING_BANK_REVIEW,
            applicant_snapshot=payload.applicant_snapshot,
            loan_amount_requested=payload.loan_amount_requested,
            loan_tenure_months=payload.loan_tenure_months,
            loan_purpose=payload.loan_purpose,
            kyc_status=payload.kyc_status,
            kyc_result_snapshot=payload.kyc_result_snapshot,
            kyc_completed_at=now,
        )
        self.db.add(app)
        await self.db.flush()
        return app

    async def get_by_external_id(self, external_id: str) -> LoanApplication:
        return await self._get_one(LoanApplication.external_application_id, external_id)

    async def get_by_id(self, app_id: str) -> LoanApplication:
        return await self._get_one(LoanApplication.id, uuid.UUID(app_id))

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        statuses_filter: Optional[List[str]] = None,
    ) -> LoanApplicationListResponse:
        where = []
        if statuses_filter:
            where.append(LoanApplication.pipeline_status.in_(statuses_filter))
        elif status_filter:
            where.append(LoanApplication.pipeline_status == status_filter)

        total = (
            await self.db.execute(
                select(func.count()).select_from(LoanApplication).where(*where)
            )
        ).scalar_one()

        rows = (
            await self.db.execute(
                select(LoanApplication)
                .where(*where)
                .order_by(desc(LoanApplication.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()

        return LoanApplicationListResponse(
            items=[LoanApplicationSummary.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def save_analyzer_selection(
        self, app_id: str, payload: AnalyzerSelectionRequest, user_id: str
    ) -> LoanApplication:
        app = await self.get_by_id(app_id)
        now = self._now()
        app.active_analyzers = payload.active_analyzers
        app.analyzers_selected_by = uuid.UUID(user_id)
        app.analyzers_selected_at = now
        app.updated_at = now
        await self.db.flush()
        return app

    async def set_decisioning_in_progress(self, app_id: str) -> LoanApplication:
        app = await self.get_by_id(app_id)
        now = self._now()
        app.pipeline_status = PipelineStatus.DECISIONING_IN_PROGRESS
        app.updated_at = now
        await self.db.flush()
        return app

    async def save_decisioning_result(
        self, app_id: str, payload: DecisioningResultPatch
    ) -> LoanApplication:
        return await self._apply_decisioning_result(await self.get_by_id(app_id), payload)

    async def save_decisioning_result_by_external(
        self, external_id: str, payload: DecisioningResultPatch
    ) -> LoanApplication:
        return await self._apply_decisioning_result(
            await self.get_by_external_id(external_id), payload
        )

    async def _apply_decisioning_result(
        self, app: LoanApplication, payload: DecisioningResultPatch
    ) -> LoanApplication:
        now = self._now()
        app.pipeline_status = PipelineStatus.AWAITING_BANK_APPROVAL
        app.llm_decision = payload.llm_decision
        app.llm_risk_tier = payload.llm_risk_tier
        app.llm_risk_score = payload.llm_risk_score
        app.llm_approved_amount = payload.llm_approved_amount
        app.llm_interest_rate = payload.llm_interest_rate
        app.llm_tenure_months = payload.llm_tenure_months
        app.llm_counter_offer_options = payload.llm_counter_offer_options
        app.decisioning_result_snapshot = payload.decisioning_result_snapshot
        app.decisioning_completed_at = now
        app.updated_at = now
        await self.db.flush()
        return app

    async def save_bank_decision(
        self, app_id: str, payload: BankDecisionRequest, user_id: str
    ) -> LoanApplication:
        app = await self.get_by_id(app_id)
        now = self._now()
        app.bank_final_decision = payload.final_decision
        app.bank_approved_amount = payload.approved_amount if payload.approved_amount is not None else app.llm_approved_amount
        app.bank_interest_rate = payload.interest_rate if payload.interest_rate is not None else app.llm_interest_rate
        app.bank_tenure_months = payload.tenure_months if payload.tenure_months is not None else app.llm_tenure_months
        app.bank_override_reason = payload.override_reason
        app.bank_decided_by = uuid.UUID(user_id)
        app.bank_decided_at = now
        app.updated_at = now
        app.pipeline_status = (
            PipelineStatus.BANK_DECLINED
            if payload.final_decision == "DECLINE"
            else PipelineStatus.AWAITING_APPLICANT_RESPONSE
        )
        await self.db.flush()
        return app

    async def set_awaiting_signature(self, external_id: str) -> LoanApplication:
        app = await self.get_by_external_id(external_id)
        now = self._now()
        app.pipeline_status = PipelineStatus.AWAITING_SIGNATURE
        app.applicant_accepted = True
        app.applicant_responded_at = now
        app.updated_at = now
        await self.db.flush()
        return app

    async def set_cancelled(self, external_id: str) -> LoanApplication:
        app = await self.get_by_external_id(external_id)
        now = self._now()
        app.pipeline_status = PipelineStatus.CANCELLED
        app.applicant_accepted = False
        app.applicant_responded_at = now
        app.updated_at = now
        await self.db.flush()
        return app

    async def save_signature(self, external_id: str, payload: SignaturePatch) -> LoanApplication:
        app = await self.get_by_external_id(external_id)
        now = self._now()
        app.signature_full_name = payload.full_name
        app.signature_agreed = payload.agreed
        app.signature_ip = payload.ip
        app.signature_user_agent = payload.user_agent
        app.signed_at = now
        app.pipeline_status = PipelineStatus.SIGNATURE_COMPLETE
        app.updated_at = now
        await self.db.flush()
        return app

    async def save_disbursement(self, external_id: str, payload: DisbursementPatch) -> LoanApplication:
        app = await self.get_by_external_id(external_id)
        now = self._now()
        app.disbursement_transaction_id = payload.transaction_id
        app.disbursed_amount = payload.disbursed_amount
        app.disbursement_receipt_snapshot = payload.disbursement_receipt_snapshot
        app.disbursed_at = now
        app.pipeline_status = PipelineStatus.DISBURSED
        app.updated_at = now
        await self.db.flush()
        return app
