import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.node_audit import NodeAuditLog

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_node_log(
        self,
        application_id: str,
        agent_name: str,
        node_name: str,
        input_state: dict,
        output_state: dict = None,
        status: str = "SUCCESS",
        error_message: str = None,
        execution_time_ms: int = 0
    ):
        log_entry = NodeAuditLog(
            application_id=application_id,
            agent_name=agent_name,
            node_name=node_name,
            input_state=input_state,
            output_state=output_state,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms
        )
        self.session.add(log_entry)
        await self.session.commit()
