from sqlalchemy.ext.asyncio import AsyncSession

from src.models.service_audit import ServiceAuditLog


class ServiceAuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_log(
        self,
        *,
        application_id: str,
        correlation_id: str | None,
        agent_name: str,
        operation_name: str,
        request_payload: dict | None,
        response_payload: dict | None,
        status: str,
        error_message: str | None,
        execution_time_ms: int,
    ) -> None:
        log_entry = ServiceAuditLog(
            application_id=application_id,
            correlation_id=correlation_id,
            agent_name=agent_name,
            operation_name=operation_name,
            request_payload=request_payload,
            response_payload=response_payload,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )
        self.session.add(log_entry)
        await self.session.commit()
