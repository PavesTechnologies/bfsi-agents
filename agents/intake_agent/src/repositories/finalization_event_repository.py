"""
Finalization Event Repository

Persistence-only access layer for LoanFinalizationEvent audit records.
No domain or framework imports; insert/update logic only.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import LoanFinalizationEvent


class FinalizationEventRepository:
    """Repository for LoanFinalizationEvent audit records."""

    async def create_event(
        self,
        session: AsyncSession,
        *,
        application_id: UUID,
        status: str,
        response_payload: dict[str, Any],
        callback_result: dict[str, Any] | None = None,
    ) -> LoanFinalizationEvent:
        """
        Create a new finalization event audit record.

        The response_payload and callback_result are stored as JSONB.
        """
        event = LoanFinalizationEvent(
            application_id=application_id,
            status=status,
            response_payload=response_payload or {},
            callback_result=callback_result,
        )
        session.add(event)
        await session.flush()
        return event
