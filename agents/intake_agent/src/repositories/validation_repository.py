from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import IntakeValidationResult

class ValidationRepository:

    async def save(
        self,
        session: AsyncSession,
        application_id,
        field_name,
        result
    ):
        record = IntakeValidationResult(
            application_id=application_id,
            field_name=field_name,
            reason_code=result.reason_code.value,
            message=result.message
        )
        session.add(record)
