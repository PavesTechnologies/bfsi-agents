"""
GET /applications          — paginated list with filters
GET /applications/{id}     — full detail (all agents merged)
GET /applications/{id}/timeline — reconstructed event timeline
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import require_officer
from src.models.admin_models import HumanReviewDecision, HumanReviewQueue, LenderUser
from src.models.external_models import (
    address_table,
    aml_checks_table,
    applicant_table,
    asset_table,
    disbursement_records_table,
    employment_table,
    identity_checks_table,
    income_table,
    kyc_cases_table,
    liability_table,
    loan_application_table,
    pgsql_document_table,
    risk_decisions_table,
    underwriting_decisions_table,
)
from src.db.session import (
    get_admin_db,
    get_decisioning_db,
    get_disbursement_db,
    get_intake_db,
    get_kyc_db,
)
from src.schemas.applications import (
    AddressSchema,
    AmlCheckSchema,
    ApplicantSchema,
    ApplicationDetailSchema,
    ApplicationSummarySchema,
    AssetSchema,
    CounterOfferOptionSchema,
    DisbursementSchema,
    DocumentSchema,
    EmploymentSchema,
    HumanReviewDecisionSchema,
    HumanReviewSummarySchema,
    IdentityCheckSchema,
    IncomeSchema,
    KycResultSchema,
    LiabilitySchema,
    LoanApplicationSchema,
    PaginatedApplicationsResponse,
    TimelineEventSchema,
    UnderwritingResultSchema,
)

router = APIRouter(prefix="/applications", tags=["applications"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row) -> dict:
    return dict(row._mapping)


def _float(val) -> Optional[float]:
    return float(val) if val is not None else None


def _str_id(val) -> Optional[str]:
    return str(val) if val is not None else None


async def _fetch_underwriting(app_ids: list[str], decisioning_db: AsyncSession) -> dict:
    """Return dict of application_id → underwriting row."""
    if not app_ids:
        return {}
    rows = await decisioning_db.execute(
        select(underwriting_decisions_table).where(
            underwriting_decisions_table.c.application_id.in_(app_ids)
        )
    )
    return {row.application_id: _row_to_dict(row) for row in rows}


async def _fetch_human_review(app_ids: list[str], admin_db: AsyncSession) -> dict:
    """Return dict of application_id → HumanReviewQueue ORM row."""
    if not app_ids:
        return {}
    result = await admin_db.execute(
        select(HumanReviewQueue).where(
            HumanReviewQueue.application_id.in_(app_ids)
        )
    )
    return {q.application_id: q for q in result.scalars().all()}


# ---------------------------------------------------------------------------
# GET /applications
# ---------------------------------------------------------------------------

@router.get("", response_model=PaginatedApplicationsResponse)
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by application_status"),
    risk_tier: Optional[str] = Query(None, description="Filter by risk tier (A/B/C/F)"),
    decision: Optional[str] = Query(None, description="Filter by AI decision"),
    human_review_status: Optional[str] = Query(None, description="Filter by human review status"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="Search by applicant name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user=Depends(require_officer),
    intake_db: AsyncSession = Depends(get_intake_db),
    decisioning_db: AsyncSession = Depends(get_decisioning_db),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    offset = (page - 1) * page_size

    # Build intake JOIN query: loan_application LEFT JOIN applicant (primary)
    base_q = (
        select(
            loan_application_table,
            applicant_table.c.applicant_id,
            applicant_table.c.first_name,
            applicant_table.c.last_name,
            applicant_table.c.email,
        )
        .outerjoin(
            applicant_table,
            and_(
                applicant_table.c.application_id == loan_application_table.c.application_id,
                applicant_table.c.applicant_role == "primary",
            ),
        )
    )

    filters = []
    if status:
        filters.append(loan_application_table.c.application_status == status)
    if date_from:
        filters.append(loan_application_table.c.created_at >= date_from)
    if date_to:
        filters.append(loan_application_table.c.created_at <= date_to)
    if search:
        term = f"%{search}%"
        filters.append(
            or_(
                (applicant_table.c.first_name + " " + applicant_table.c.last_name).ilike(term),
                applicant_table.c.email.ilike(term),
                loan_application_table.c.application_id.cast(type_=__import__("sqlalchemy").String).ilike(term),
            )
        )
    if filters:
        base_q = base_q.where(and_(*filters))

    # Count query
    count_q = select(func.count()).select_from(base_q.subquery())

    # Paginated data query
    data_q = (
        base_q.order_by(loan_application_table.c.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    # Run count then data — same session cannot handle concurrent operations
    count_result = await intake_db.execute(count_q)
    total = count_result.scalar() or 0
    data_result = await intake_db.execute(data_q)
    rows = data_result.fetchall()

    if not rows:
        return PaginatedApplicationsResponse(total=total, page=page, page_size=page_size, items=[])

    app_ids = [str(r.application_id) for r in rows]

    # Fetch decisioning + human review in parallel
    uw_map, hr_map = await asyncio.gather(
        _fetch_underwriting(app_ids, decisioning_db),
        _fetch_human_review(app_ids, admin_db),
    )

    # Apply risk_tier / decision / human_review_status post-filters
    items = []
    for row in rows:
        app_id = str(row.application_id)
        uw = uw_map.get(app_id)
        hr = hr_map.get(app_id)

        ai_decision = uw["decision"] if uw else None
        rt = uw["risk_tier"] if uw else None
        rs = _float(uw["risk_score"]) if uw else None
        hr_status = hr.status if hr else None

        if risk_tier and rt != risk_tier:
            continue
        if decision and ai_decision != decision:
            continue
        if human_review_status and hr_status != human_review_status:
            continue

        first = row.first_name or ""
        last = row.last_name or ""
        name = f"{first} {last}".strip() or "Unknown"

        items.append(
            ApplicationSummarySchema(
                application_id=app_id,
                applicant_name=name,
                email=row.email,
                loan_type=row.loan_type,
                requested_amount=_float(row.requested_amount),
                application_status=row.application_status,
                ai_decision=ai_decision,
                risk_tier=rt,
                risk_score=rs,
                human_review_status=hr_status,
                created_at=row.created_at,
            )
        )

    return PaginatedApplicationsResponse(
        total=total, page=page, page_size=page_size, items=items
    )


# ---------------------------------------------------------------------------
# GET /applications/{application_id}
# ---------------------------------------------------------------------------

@router.get("/{application_id}", response_model=ApplicationDetailSchema)
async def get_application_detail(
    application_id: str,
    _user=Depends(require_officer),
    intake_db: AsyncSession = Depends(get_intake_db),
    kyc_db: AsyncSession = Depends(get_kyc_db),
    decisioning_db: AsyncSession = Depends(get_decisioning_db),
    disbursement_db: AsyncSession = Depends(get_disbursement_db),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    # ---- 1. Intake: loan_application ----
    app_result = await intake_db.execute(
        select(loan_application_table).where(
            loan_application_table.c.application_id == application_id
        )
    )
    app_row = app_result.fetchone()
    if app_row is None:
        from src.core.exceptions import NotFoundException
        raise NotFoundException(f"Application {application_id} not found")

    app_schema = LoanApplicationSchema(
        application_id=str(app_row.application_id),
        loan_type=app_row.loan_type,
        credit_type=app_row.credit_type,
        loan_purpose=app_row.loan_purpose,
        requested_amount=_float(app_row.requested_amount),
        requested_term_months=app_row.requested_term_months,
        preferred_payment_day=app_row.preferred_payment_day,
        origination_channel=app_row.origination_channel,
        application_status=app_row.application_status,
        created_at=app_row.created_at,
        updated_at=app_row.updated_at,
    )

    # ---- 2. Intake: applicant + nested data (parallel) ----
    applicant_result = await intake_db.execute(
        select(applicant_table).where(
            applicant_table.c.application_id == application_id
        )
    )
    applicant_rows = applicant_result.fetchall()

    applicant_schema = None
    if applicant_rows:
        # Use primary applicant; fall back to first
        primary = next(
            (r for r in applicant_rows if r.applicant_role == "primary"),
            applicant_rows[0],
        )
        appl_id = primary.applicant_id

        # Fetch all sub-tables for primary applicant sequentially (same session)
        addr_res = await intake_db.execute(
            select(address_table).where(address_table.c.applicant_id == appl_id)
        )
        empl_res = await intake_db.execute(
            select(employment_table).where(employment_table.c.applicant_id == appl_id)
        )
        inc_res = await intake_db.execute(
            select(income_table).where(income_table.c.applicant_id == appl_id)
        )
        asset_res = await intake_db.execute(
            select(asset_table).where(asset_table.c.applicant_id == appl_id)
        )
        liab_res = await intake_db.execute(
            select(liability_table).where(liability_table.c.applicant_id == appl_id)
        )
        doc_res = await intake_db.execute(
            select(pgsql_document_table).where(
                pgsql_document_table.c.application_id == application_id
            )
        )

        addresses = [
            AddressSchema(
                address_id=str(r.address_id),
                address_type=r.address_type,
                address_line1=r.address_line1,
                address_line2=r.address_line2,
                city=r.city,
                state=r.state,
                zip_code=r.zip_code,
                country=r.country,
                housing_status=r.housing_status,
                monthly_housing_payment=_float(r.monthly_housing_payment),
                years_at_address=r.years_at_address,
                months_at_address=r.months_at_address,
            )
            for r in addr_res.fetchall()
        ]

        empl_rows = empl_res.fetchall()
        employment = None
        if empl_rows:
            e = empl_rows[0]
            employment = EmploymentSchema(
                employment_id=str(e.employment_id),
                employment_type=e.employment_type,
                employment_status=e.employment_status,
                employer_name=e.employer_name,
                job_title=e.job_title,
                start_date=e.start_date,
                experience=e.experience,
                self_employed_flag=e.self_employed_flag,
                gross_monthly_income=_float(e.gross_monthly_income),
            )

        incomes = [
            IncomeSchema(
                income_id=str(r.income_id),
                income_type=r.income_type,
                description=r.description,
                monthly_amount=_float(r.monthly_amount),
                income_frequency=r.income_frequency,
            )
            for r in inc_res.fetchall()
        ]

        assets = [
            AssetSchema(
                asset_id=str(r.asset_id),
                asset_type=r.asset_type,
                institution_name=r.institution_name,
                value=_float(r.value),
                ownership_type=r.ownership_type,
            )
            for r in asset_res.fetchall()
        ]

        liabilities = [
            LiabilitySchema(
                liability_id=str(r.liability_id),
                liability_type=r.liability_type,
                creditor_name=r.creditor_name,
                outstanding_balance=_float(r.outstanding_balance),
                monthly_payment=_float(r.monthly_payment),
                months_remaining=r.months_remaining,
                delinquent_flag=r.delinquent_flag,
            )
            for r in liab_res.fetchall()
        ]

        documents = [
            DocumentSchema(
                document_id=str(r.id),
                document_type=r.document_type,
                file_name=r.file_name,
                mime_type=r.mime_type,
                file_size=r.file_size,
                uploaded_at=r.uploaded_at,
                is_low_quality=r.is_low_quality,
            )
            for r in doc_res.fetchall()
        ]

        applicant_schema = ApplicantSchema(
            applicant_id=str(primary.applicant_id),
            application_id=str(primary.application_id),
            first_name=primary.first_name,
            middle_name=primary.middle_name,
            last_name=primary.last_name,
            suffix=primary.suffix,
            date_of_birth=primary.date_of_birth,
            applicant_role=primary.applicant_role,
            email=primary.email,
            ssn_last4=primary.ssn_last4,
            phone_number=primary.phone_number,
            gender=primary.gender,
            citizenship_status=primary.citizenship_status,
            addresses=addresses,
            employment=employment,
            incomes=incomes,
            assets=assets,
            liabilities=liabilities,
        )
    else:
        documents = []
        appl_id = None

    # ---- 3. KYC (keyed by applicant_id) ----
    kyc_schema = None
    if appl_id is not None:
        kyc_result = await kyc_db.execute(
            select(kyc_cases_table).where(
                kyc_cases_table.c.applicant_id == appl_id
            ).order_by(kyc_cases_table.c.created_at.desc()).limit(1)
        )
        kyc_row = kyc_result.fetchone()
        if kyc_row:
            kyc_id = kyc_row.id
            aml_res = await kyc_db.execute(
                select(aml_checks_table).where(aml_checks_table.c.kyc_id == kyc_id)
            )
            identity_res = await kyc_db.execute(
                select(identity_checks_table).where(identity_checks_table.c.kyc_id == kyc_id)
            )
            risk_res = await kyc_db.execute(
                select(risk_decisions_table).where(risk_decisions_table.c.kyc_id == kyc_id)
            )

            aml_row = aml_res.fetchone()
            identity_row = identity_res.fetchone()
            risk_row = risk_res.fetchone()

            kyc_schema = KycResultSchema(
                kyc_case_id=str(kyc_row.id),
                applicant_id=str(kyc_row.applicant_id),
                status=kyc_row.status,
                confidence_score=kyc_row.confidence_score,
                rules_version=kyc_row.rules_version,
                created_at=kyc_row.created_at,
                completed_at=kyc_row.completed_at,
                risk_decision=risk_row.final_status if risk_row else None,
                identity_check=IdentityCheckSchema(
                    id=str(identity_row.id),
                    final_status=identity_row.final_status,
                    aggregated_score=identity_row.aggregated_score,
                    hard_fail_triggered=identity_row.hard_fail_triggered,
                    ssn_valid=identity_row.ssn_valid,
                    name_ssn_match=identity_row.name_ssn_match,
                    dob_ssn_match=identity_row.dob_ssn_match,
                    deceased_flag=identity_row.deceased_flag,
                ) if identity_row else None,
                aml_check=AmlCheckSchema(
                    id=str(aml_row.id),
                    ofac_match=aml_row.ofac_match,
                    ofac_confidence=aml_row.ofac_confidence,
                    pep_match=aml_row.pep_match,
                    aml_score=aml_row.aml_score,
                    flags=aml_row.flags,
                ) if aml_row else None,
            )

    # ---- 4. Underwriting ----
    uw_result = await decisioning_db.execute(
        select(underwriting_decisions_table).where(
            underwriting_decisions_table.c.application_id == application_id
        ).order_by(underwriting_decisions_table.c.created_at.desc()).limit(1)
    )
    uw_row = uw_result.fetchone()
    uw_schema = None
    if uw_row:
        counter_options = None
        if uw_row.counter_offer_data and isinstance(uw_row.counter_offer_data, dict):
            raw_options = uw_row.counter_offer_data.get("generated_options", [])
            counter_options = [
                CounterOfferOptionSchema(
                    offer_id=o.get("offer_id", ""),
                    principal_amount=o.get("principal_amount", 0),
                    tenure_months=o.get("tenure_months", 0),
                    interest_rate=o.get("interest_rate", 0),
                    monthly_emi=o.get("monthly_emi", 0),
                    label=o.get("label", ""),
                )
                for o in raw_options
            ]
        uw_schema = UnderwritingResultSchema(
            id=str(uw_row.id),
            decision=uw_row.decision,
            risk_tier=uw_row.risk_tier,
            risk_score=uw_row.risk_score,
            approved_amount=_float(uw_row.approved_amount),
            disbursement_amount=_float(uw_row.disbursement_amount),
            interest_rate=uw_row.interest_rate,
            tenure_months=uw_row.tenure_months,
            explanation=uw_row.explanation,
            decline_reason=uw_row.decline_reason,
            reasoning_steps=uw_row.reasoning_steps or [],
            counter_offer_options=counter_options,
            created_at=uw_row.created_at,
        )

    # ---- 5. Disbursement ----
    disb_result = await disbursement_db.execute(
        select(disbursement_records_table).where(
            disbursement_records_table.c.application_id == application_id
        ).order_by(disbursement_records_table.c.created_at.desc()).limit(1)
    )
    disb_row = disb_result.fetchone()
    disb_schema = None
    if disb_row:
        disb_schema = DisbursementSchema(
            id=str(disb_row.id),
            transaction_id=disb_row.transaction_id,
            status=disb_row.status,
            disbursement_amount=_float(disb_row.disbursement_amount),
            monthly_emi=_float(disb_row.monthly_emi),
            total_interest=_float(disb_row.total_interest),
            total_repayment=_float(disb_row.total_repayment),
            transfer_timestamp=disb_row.transfer_timestamp,
            repayment_schedule=disb_row.repayment_schedule,
            created_at=disb_row.created_at,
        )

    # ---- 6. Human review (admin_db) ----
    hr_result = await admin_db.execute(
        select(HumanReviewQueue).where(
            HumanReviewQueue.application_id == application_id
        )
    )
    hr_queue = hr_result.scalar_one_or_none()
    hr_schema = None
    if hr_queue:
        assignee_name = None
        if hr_queue.assigned_to:
            u = await admin_db.get(LenderUser, hr_queue.assigned_to)
            assignee_name = u.full_name if u else None

        # Latest decision
        dec_result = await admin_db.execute(
            select(HumanReviewDecision)
            .where(HumanReviewDecision.queue_id == hr_queue.id)
            .order_by(HumanReviewDecision.created_at.desc())
            .limit(1)
        )
        dec_row = dec_result.scalar_one_or_none()
        latest_decision = None
        if dec_row:
            reviewer = await admin_db.get(LenderUser, dec_row.reviewed_by)
            latest_decision = HumanReviewDecisionSchema(
                id=str(dec_row.id),
                decision=dec_row.decision,
                override_amount=dec_row.override_amount,
                override_rate=dec_row.override_rate,
                override_tenure=dec_row.override_tenure,
                selected_offer_id=dec_row.selected_offer_id,
                notes=dec_row.notes,
                reviewed_by=reviewer.full_name if reviewer else str(dec_row.reviewed_by),
                created_at=dec_row.created_at,
            )

        hr_schema = HumanReviewSummarySchema(
            queue_id=str(hr_queue.id),
            status=hr_queue.status,
            assigned_to=assignee_name,
            ai_decision=hr_queue.ai_decision,
            ai_risk_tier=hr_queue.ai_risk_tier,
            ai_risk_score=hr_queue.ai_risk_score,
            ai_suggested_amount=hr_queue.ai_suggested_amount,
            ai_suggested_rate=hr_queue.ai_suggested_rate,
            ai_suggested_tenure=hr_queue.ai_suggested_tenure,
            ai_counter_options=hr_queue.ai_counter_options,
            ai_reasoning=hr_queue.ai_reasoning,
            ai_decline_reason=hr_queue.ai_decline_reason,
            created_at=hr_queue.created_at,
            assigned_at=hr_queue.assigned_at,
            decided_at=hr_queue.decided_at,
            latest_decision=latest_decision,
        )

    return ApplicationDetailSchema(
        application=app_schema,
        applicant=applicant_schema,
        documents=documents,
        kyc=kyc_schema,
        underwriting=uw_schema,
        disbursement=disb_schema,
        human_review=hr_schema,
    )


# ---------------------------------------------------------------------------
# GET /applications/{application_id}/timeline
# ---------------------------------------------------------------------------

@router.get("/{application_id}/timeline", response_model=list[TimelineEventSchema])
async def get_application_timeline(
    application_id: str,
    _user=Depends(require_officer),
    intake_db: AsyncSession = Depends(get_intake_db),
    kyc_db: AsyncSession = Depends(get_kyc_db),
    decisioning_db: AsyncSession = Depends(get_decisioning_db),
    disbursement_db: AsyncSession = Depends(get_disbursement_db),
    admin_db: AsyncSession = Depends(get_admin_db),
):
    """
    Reconstruct a timeline of pipeline events from DB timestamps.
    The orchestrator uses in-memory SSE (not persisted), so we rebuild
    from record created_at timestamps across all agent databases.
    """
    events: list[TimelineEventSchema] = []

    # ---- Intake: application created ----
    app_result = await intake_db.execute(
        select(
            loan_application_table.c.created_at,
            loan_application_table.c.application_status,
        ).where(loan_application_table.c.application_id == application_id)
    )
    app_row = app_result.fetchone()
    if app_row and app_row.created_at:
        events.append(TimelineEventSchema(
            timestamp=app_row.created_at,
            event="APPLICATION_SUBMITTED",
            stage="INTAKE",
            status="complete",
            message="Loan application submitted by applicant",
        ))

    # ---- KYC ----
    applicant_result = await intake_db.execute(
        select(applicant_table.c.applicant_id).where(
            and_(
                applicant_table.c.application_id == application_id,
                applicant_table.c.applicant_role == "primary",
            )
        ).limit(1)
    )
    appl_row = applicant_result.fetchone()
    if appl_row:
        kyc_result = await kyc_db.execute(
            select(kyc_cases_table).where(
                kyc_cases_table.c.applicant_id == appl_row.applicant_id
            ).order_by(kyc_cases_table.c.created_at.desc()).limit(1)
        )
        kyc_row = kyc_result.fetchone()
        if kyc_row:
            events.append(TimelineEventSchema(
                timestamp=kyc_row.created_at,
                event="KYC_STARTED",
                stage="KYC",
                status="complete",
                message="Identity verification started",
            ))
            if kyc_row.completed_at:
                kyc_status_map = {
                    "PASSED": ("KYC_PASSED", "complete", "Identity verification passed"),
                    "FAILED": ("KYC_FAILED", "error", "Identity verification failed"),
                    "REVIEW": ("KYC_REVIEW", "warning", "Identity verification requires manual review"),
                }
                evt, status, msg = kyc_status_map.get(
                    kyc_row.status, ("KYC_COMPLETED", "complete", "KYC completed")
                )
                events.append(TimelineEventSchema(
                    timestamp=kyc_row.completed_at,
                    event=evt,
                    stage="KYC",
                    status=status,
                    message=msg,
                ))

    # ---- Underwriting ----
    uw_result = await decisioning_db.execute(
        select(
            underwriting_decisions_table.c.created_at,
            underwriting_decisions_table.c.decision,
            underwriting_decisions_table.c.risk_tier,
        ).where(
            underwriting_decisions_table.c.application_id == application_id
        ).order_by(underwriting_decisions_table.c.created_at.asc())
    )
    uw_rows = uw_result.fetchall()
    for uw_row in uw_rows:
        decision_map = {
            "APPROVE": ("AI_RECOMMENDED_APPROVE", "complete", "AI recommended approval"),
            "COUNTER_OFFER": ("AI_RECOMMENDED_COUNTER_OFFER", "warning", "AI generated counter offer options"),
            "DECLINE": ("AI_RECOMMENDED_DECLINE", "error", "AI recommended decline"),
        }
        evt, status, msg = decision_map.get(
            uw_row.decision, ("UNDERWRITING_COMPLETED", "complete", "Underwriting completed")
        )
        tier_note = f" (Risk tier: {uw_row.risk_tier})" if uw_row.risk_tier else ""
        events.append(TimelineEventSchema(
            timestamp=uw_row.created_at,
            event=evt,
            stage="UNDERWRITING",
            status=status,
            message=msg + tier_note,
        ))

    # ---- Human review ----
    hr_result = await admin_db.execute(
        select(HumanReviewQueue).where(HumanReviewQueue.application_id == application_id)
    )
    hr_queue = hr_result.scalar_one_or_none()
    if hr_queue:
        events.append(TimelineEventSchema(
            timestamp=hr_queue.created_at,
            event="HUMAN_REVIEW_QUEUED",
            stage="HUMAN_REVIEW",
            status="complete",
            message="Application queued for bank officer review",
        ))
        if hr_queue.assigned_at:
            events.append(TimelineEventSchema(
                timestamp=hr_queue.assigned_at,
                event="HUMAN_REVIEW_ASSIGNED",
                stage="HUMAN_REVIEW",
                status="complete",
                message="Application assigned to a loan officer",
            ))
        if hr_queue.decided_at:
            status_map = {
                "APPROVED": ("HUMAN_REVIEW_APPROVED", "complete", "Bank officer approved the application"),
                "REJECTED": ("HUMAN_REVIEW_REJECTED", "error", "Bank officer rejected the application"),
                "OVERRIDDEN": ("HUMAN_REVIEW_APPROVED_WITH_OVERRIDE", "complete", "Bank officer approved with modified terms"),
            }
            evt, status, msg = status_map.get(
                hr_queue.status, ("HUMAN_REVIEW_DECIDED", "complete", "Human review completed")
            )
            events.append(TimelineEventSchema(
                timestamp=hr_queue.decided_at,
                event=evt,
                stage="HUMAN_REVIEW",
                status=status,
                message=msg,
            ))

    # ---- Disbursement ----
    disb_result = await disbursement_db.execute(
        select(
            disbursement_records_table.c.created_at,
            disbursement_records_table.c.transfer_timestamp,
            disbursement_records_table.c.status,
            disbursement_records_table.c.disbursement_amount,
        ).where(
            disbursement_records_table.c.application_id == application_id
        ).order_by(disbursement_records_table.c.created_at.asc())
    )
    disb_rows = disb_result.fetchall()
    for disb_row in disb_rows:
        events.append(TimelineEventSchema(
            timestamp=disb_row.created_at,
            event="DISBURSEMENT_INITIATED",
            stage="DISBURSEMENT",
            status="complete",
            message="Loan disbursement initiated",
        ))
        if disb_row.transfer_timestamp and disb_row.status == "COMPLETED":
            events.append(TimelineEventSchema(
                timestamp=disb_row.transfer_timestamp,
                event="FUNDS_DISBURSED",
                stage="DISBURSEMENT",
                status="complete",
                message=f"Funds disbursed: ${_float(disb_row.disbursement_amount):,.2f}" if disb_row.disbursement_amount else "Funds disbursed",
            ))

    # Sort all events chronologically
    events.sort(key=lambda e: e.timestamp)
    return events
