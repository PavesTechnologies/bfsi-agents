from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.intake_repo.loan_intake_repo import (
    LoanIntakeDAO as LoanRepository,
)
from src.utils.finalize.finalize_output import (
    build_canonical,
    map_applicants,
    map_application,
    validate_schema,
)
from src.utils.finalize.json_safe import to_json_safe


class LoanFinalizationService:
    def __init__(self, db: AsyncSession, callback_client):
        self.db = db
        self.repo = LoanRepository(db)
        self.callback = callback_client

    async def finalize(
        self, application_id, callback_url, enrichments=None, errors=None
    ):
        try:
            loan = await self.repo.get_full_application(application_id)

            if not loan:
                return {"status": "NOT_FOUND"}

            if loan.finalized_flag:
                return {"status": "ALREADY_FINALIZED"}

            application_dict = map_application(loan)
            applicants_dict = map_applicants(loan)
            evidence = await self.repo.get_documents_as_evidence(application_id)

            canonical = build_canonical(
                application_dict, applicants_dict, enrichments or {}, evidence
            )
            canonical = to_json_safe(canonical)

            # VALIDATION
            try:
                validate_schema(canonical)
                status = "PARTIAL_SUCCESS" if errors else "SUCCESS"
            except Exception:
                status = "FAILURE"

            # CALLBACK
            callback_result = await self.callback.send(
                callback_url,
                status,
                {"application_id": str(application_id), "data": canonical},
            )

            # AUDIT
            await self.repo.save_event(
                application_id, status, canonical, callback_result
            )
            await self.repo.mark_finalized(loan)

            await self.db.commit()

            return {
                "status": status,
                "callback_ok": callback_result.get("ok"),
                "application_id": str(application_id),
            }

        except Exception as e:
            await self.db.rollback()
            return {"status": "SYSTEM_ERROR", "error": str(e)}
