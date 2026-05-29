import uuid
import datetime
from typing import Any, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.counter_offer import CounterOfferEditLog, CounterOfferSession, CounterOfferStatus
from src.models.loan_application import LoanApplication, PipelineStatus
from src.models.bank_rule import BankRule
from src.services.orchestrator_client import OrchestratorClient
from src.schemas.counter_offer import (
    CounterOfferSessionCreateInternal,
    OfferOptionCreateRequest,
    OfferOptionUpdateRequest,
    RecommendRequest,
)
from src.utils.finance import compute_emi

_404 = status.HTTP_404_NOT_FOUND
_400 = status.HTTP_400_BAD_REQUEST
_409 = status.HTTP_409_CONFLICT

_DEFAULT_ORIGINATION_FEE_PCT = 0.02
_EXPIRY_DAYS = 10
_PROTECTED_IDS = frozenset({"CO1", "CO2", "CO3"})


class CounterOfferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    async def _get_session(self, session_id: uuid.UUID) -> CounterOfferSession:
        row = (
            await self.db.execute(
                select(CounterOfferSession).where(CounterOfferSession.id == session_id)
            )
        ).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=_404, detail=f"Counter offer session not found: {session_id}")
        return row

    async def _get_origination_fee_pct(self) -> float:
        row = (
            await self.db.execute(
                select(BankRule).where(BankRule.rule_key == "origination_fee_pct")
            )
        ).scalar_one_or_none()
        if row and row.current_value is not None:
            try:
                return float(row.current_value)
            except (TypeError, ValueError):
                pass
        return _DEFAULT_ORIGINATION_FEE_PCT

    def _recalculate(self, option: dict, max_affordable_emi: float, fee_pct: float) -> dict:
        """Recompute all derived fields from the three editable financial inputs."""
        amount = float(option["proposed_amount"])
        rate = float(option["proposed_interest_rate"])
        months = int(option["proposed_tenure_months"])
        emi = compute_emi(amount, rate, months)
        disbursement = round(amount * (1 - fee_pct), 2)
        total = round(emi * months, 2)
        headroom = (
            round(((max_affordable_emi - emi) / max_affordable_emi) * 100, 2)
            if max_affordable_emi > 0 else 0.0
        )
        return {
            **option,
            "monthly_payment_emi": emi,
            "disbursement_amount": disbursement,
            "total_repayment": total,
            "affordability_headroom_pct": headroom,
        }

    def _sync_recommended_flag(self, options: list, recommended_id: str) -> list:
        return [{**o, "is_recommended": o["option_id"] == recommended_id} for o in options]

    async def _log_edit(
        self,
        session_id: uuid.UUID,
        option_id: Optional[str],
        field_name: str,
        old_value: Any,
        new_value: Any,
        edited_by: str,
        note: Optional[str] = None,
    ) -> None:
        self.db.add(
            CounterOfferEditLog(
                session_id=session_id,
                option_id=option_id,
                field_name=field_name,
                old_value={field_name: old_value},
                new_value={field_name: new_value},
                edited_by=uuid.UUID(edited_by),
                note=note,
            )
        )

    # ── Public interface ─────────────────────────────────────────────────────────

    async def create_session(self, payload: CounterOfferSessionCreateInternal) -> CounterOfferSession:
        app = (
            await self.db.execute(
                select(LoanApplication).where(
                    LoanApplication.external_application_id == payload.external_application_id
                )
            )
        ).scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=_404, detail="Application not found")
        if app.llm_decision != "COUNTER_OFFER":
            raise HTTPException(
                status_code=_400,
                detail=f"Application decision is {app.llm_decision!r}, expected COUNTER_OFFER",
            )

        co = payload.counter_offer_data
        now = self._now()
        expires_at = now + datetime.timedelta(days=_EXPIRY_DAYS)
        recommended_id = co.get("recommended_option_id", "CO1")
        options = self._sync_recommended_flag(co.get("generated_options", []), recommended_id)

        session = CounterOfferSession(
            application_id=app.id,
            original_request_dti=float(co.get("original_request_dti", 0)),
            max_affordable_emi=float(co.get("max_affordable_emi", 0)),
            monthly_income=float(co.get("monthly_income", 0)),
            existing_monthly_obligations=float(co.get("existing_monthly_obligations", 0)),
            qualifying_cap=float(co.get("qualifying_cap", 0)),
            counter_offer_logic=co.get("counter_offer_logic", ""),
            confidence_score=float(co.get("confidence_score", 0)),
            generated_options=options,
            current_options=options,
            recommended_option_id=recommended_id,
            recommendation_rationale=co.get("recommendation_rationale", ""),
            status=CounterOfferStatus.DRAFT,
            expires_at=expires_at,
        )
        self.db.add(session)

        app.pipeline_status = PipelineStatus.COUNTER_OFFER_REVIEW
        app.updated_at = now

        await self.db.flush()
        return session

    async def get_by_application_id(self, application_id: uuid.UUID) -> CounterOfferSession:
        row = (
            await self.db.execute(
                select(CounterOfferSession)
                .where(CounterOfferSession.application_id == application_id)
                .order_by(desc(CounterOfferSession.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=_404,
                detail="No counter offer session found for this application",
            )
        return row

    async def update_option(
        self,
        session_id: uuid.UUID,
        option_id: str,
        payload: OfferOptionUpdateRequest,
        user_id: str,
    ) -> CounterOfferSession:
        session = await self._get_session(session_id)
        if session.status != CounterOfferStatus.DRAFT:
            raise HTTPException(status_code=_409, detail=f"Session is {session.status} — edits not allowed")

        options = list(session.current_options)
        idx = next((i for i, o in enumerate(options) if o["option_id"] == option_id), None)
        if idx is None:
            raise HTTPException(status_code=_404, detail=f"Option {option_id} not found")

        old_option = options[idx]
        new_option = dict(old_option)
        editable = {
            "proposed_amount": payload.proposed_amount,
            "proposed_tenure_months": payload.proposed_tenure_months,
            "proposed_interest_rate": payload.proposed_interest_rate,
            "justification": payload.justification,
        }
        changed = {k: v for k, v in editable.items() if v is not None}
        if not changed:
            return session

        for field, value in changed.items():
            await self._log_edit(
                session_id, option_id, field,
                old_option.get(field), value,
                user_id, payload.note,
            )
            new_option[field] = value

        if changed.keys() & {"proposed_amount", "proposed_tenure_months", "proposed_interest_rate"}:
            fee_pct = await self._get_origination_fee_pct()
            new_option = self._recalculate(new_option, float(session.max_affordable_emi), fee_pct)

        options[idx] = new_option
        session.current_options = self._sync_recommended_flag(options, session.recommended_option_id)
        session.updated_at = self._now()
        await self.db.flush()
        return session

    async def add_option(
        self,
        session_id: uuid.UUID,
        payload: OfferOptionCreateRequest,
        user_id: str,
    ) -> CounterOfferSession:
        session = await self._get_session(session_id)
        if session.status != CounterOfferStatus.DRAFT:
            raise HTTPException(status_code=_409, detail=f"Session is {session.status} — additions not allowed")

        fee_pct = await self._get_origination_fee_pct()
        custom_id = f"custom-{uuid.uuid4().hex[:8]}"
        new_option = self._recalculate(
            {
                "option_id": custom_id,
                "label": payload.label,
                "proposed_amount": payload.proposed_amount,
                "proposed_tenure_months": payload.proposed_tenure_months,
                "proposed_interest_rate": payload.proposed_interest_rate,
                "justification": payload.justification,
                "is_recommended": False,
                "feasible": True,
                "monthly_payment_emi": 0.0,
                "disbursement_amount": 0.0,
                "total_repayment": 0.0,
                "affordability_headroom_pct": 0.0,
            },
            float(session.max_affordable_emi),
            fee_pct,
        )

        options = list(session.current_options) + [new_option]
        session.current_options = options
        session.updated_at = self._now()

        await self._log_edit(session_id, custom_id, "option_added", None, new_option, user_id)
        await self.db.flush()
        return session

    async def delete_option(
        self,
        session_id: uuid.UUID,
        option_id: str,
        user_id: str,
    ) -> CounterOfferSession:
        if option_id in _PROTECTED_IDS:
            raise HTTPException(
                status_code=_400,
                detail=f"Cannot delete LLM-generated option {option_id}",
            )
        session = await self._get_session(session_id)
        if session.status != CounterOfferStatus.DRAFT:
            raise HTTPException(status_code=_409, detail=f"Session is {session.status} — deletions not allowed")

        existing = {o["option_id"]: o for o in session.current_options}
        if option_id not in existing:
            raise HTTPException(status_code=_404, detail=f"Option {option_id} not found")

        await self._log_edit(session_id, option_id, "option_deleted", existing[option_id], None, user_id)

        options = [o for o in session.current_options if o["option_id"] != option_id]
        if session.recommended_option_id == option_id:
            session.recommended_option_id = "CO1"
        session.current_options = self._sync_recommended_flag(options, session.recommended_option_id)
        session.updated_at = self._now()
        await self.db.flush()
        return session

    async def set_recommended(
        self,
        session_id: uuid.UUID,
        payload: RecommendRequest,
        user_id: str,
    ) -> CounterOfferSession:
        session = await self._get_session(session_id)
        if session.status != CounterOfferStatus.DRAFT:
            raise HTTPException(status_code=_409, detail=f"Session is {session.status} — edits not allowed")

        option_ids = {o["option_id"] for o in session.current_options}
        if payload.option_id not in option_ids:
            raise HTTPException(status_code=_404, detail=f"Option {payload.option_id} not found")

        await self._log_edit(
            session_id, None, "recommended_option_id",
            session.recommended_option_id, payload.option_id,
            user_id, payload.note,
        )
        session.recommended_option_id = payload.option_id
        session.current_options = self._sync_recommended_flag(
            list(session.current_options), payload.option_id
        )
        session.updated_at = self._now()
        await self.db.flush()
        return session

    async def publish(self, session_id: uuid.UUID, user_id: str) -> CounterOfferSession:
        session = await self._get_session(session_id)
        if session.status != CounterOfferStatus.DRAFT:
            raise HTTPException(status_code=_409, detail=f"Session is already {session.status}")

        now = self._now()
        if now >= session.expires_at:
            session.status = CounterOfferStatus.EXPIRED
            await self.db.flush()
            raise HTTPException(status_code=_409, detail="Counter offer session has expired before publishing")

        app = (
            await self.db.execute(
                select(LoanApplication).where(LoanApplication.id == session.application_id)
            )
        ).scalar_one_or_none()
        if app:
            app.pipeline_status = PipelineStatus.AWAITING_APPLICANT_RESPONSE
            app.updated_at = now

        session.status = CounterOfferStatus.PUBLISHED
        session.published_by = uuid.UUID(user_id)
        session.published_at = now
        session.updated_at = now
        await self.db.flush()

        # Notify the orchestrator so it pushes a BANK_COUNTER_OFFERS_PUBLISHED SSE
        # event to the applicant's stream. Non-fatal if the call fails.
        if app:
            try:
                await OrchestratorClient().notify_counter_offers_published(
                    external_application_id=app.external_application_id,
                    current_options=list(session.current_options),
                )
            except Exception as exc:
                print(f"Warning: orchestrator notification failed after publish: {exc}")

        return session

    async def record_applicant_accept(
        self, external_application_id: str, accepted_option_id: str
    ) -> CounterOfferSession:
        """Record applicant's acceptance of one counter-offer option.

        Sets session status → APPLICANT_RESPONDED and advances the application
        to AWAITING_SIGNATURE in a single transaction.
        """
        app = (
            await self.db.execute(
                select(LoanApplication).where(
                    LoanApplication.external_application_id == external_application_id
                )
            )
        ).scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=_404, detail="Application not found")

        session = await self.get_by_application_id(app.id)
        if session.status != CounterOfferStatus.PUBLISHED:
            raise HTTPException(
                status_code=_409,
                detail=f"Counter offer session is {session.status} — cannot record acceptance",
            )

        option_ids = {o["option_id"] for o in session.current_options}
        if accepted_option_id not in option_ids:
            raise HTTPException(
                status_code=_404, detail=f"Option {accepted_option_id} not found in published offers"
            )

        now = self._now()
        session.applicant_decision = "ACCEPTED"
        session.accepted_option_id = accepted_option_id
        session.status = CounterOfferStatus.APPLICANT_RESPONDED
        session.applicant_responded_at = now
        session.updated_at = now

        app.pipeline_status = PipelineStatus.AWAITING_SIGNATURE
        app.applicant_accepted = True
        app.applicant_responded_at = now
        app.updated_at = now

        await self.db.flush()
        return session

    async def record_applicant_decline(self, external_application_id: str) -> CounterOfferSession:
        """Record applicant's rejection of all counter-offer options.

        Sets session status → APPLICANT_RESPONDED and cancels the application.
        """
        app = (
            await self.db.execute(
                select(LoanApplication).where(
                    LoanApplication.external_application_id == external_application_id
                )
            )
        ).scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=_404, detail="Application not found")

        session = await self.get_by_application_id(app.id)
        if session.status != CounterOfferStatus.PUBLISHED:
            raise HTTPException(
                status_code=_409,
                detail=f"Counter offer session is {session.status} — cannot record decline",
            )

        now = self._now()
        session.applicant_decision = "DECLINED"
        session.status = CounterOfferStatus.APPLICANT_RESPONDED
        session.applicant_responded_at = now
        session.updated_at = now

        app.pipeline_status = PipelineStatus.CANCELLED
        app.applicant_accepted = False
        app.applicant_responded_at = now
        app.updated_at = now

        await self.db.flush()
        return session

    async def get_edit_log(self, session_id: uuid.UUID) -> List[CounterOfferEditLog]:
        rows = (
            await self.db.execute(
                select(CounterOfferEditLog)
                .where(CounterOfferEditLog.session_id == session_id)
                .order_by(CounterOfferEditLog.edited_at)
            )
        ).scalars().all()
        return list(rows)
