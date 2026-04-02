"""Persistent store for paused pipeline state backed by PostgreSQL."""

import json
from typing import Any, Dict, Optional

from sqlalchemy import select, delete

from src.store.database import AsyncSessionLocal
from src.store.models import PipelineStateModel


async def save_state(application_id: str, state: Dict[str, Any]) -> None:
    """Upsert pipeline state for an application into the database."""
    serialized = json.loads(json.dumps(state, default=str))
    async with AsyncSessionLocal() as session:
        existing = await session.get(PipelineStateModel, application_id)
        if existing:
            existing.state_json = serialized
        else:
            session.add(
                PipelineStateModel(
                    application_id=application_id,
                    state_json=serialized,
                )
            )
        await session.commit()


async def get_state(application_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve pipeline state for an application from the database."""
    async with AsyncSessionLocal() as session:
        result = await session.get(PipelineStateModel, application_id)
        if result:
            return result.state_json
        return None


async def clear_state(application_id: str) -> None:
    """Remove pipeline state for an application from the database."""
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(PipelineStateModel).where(
                PipelineStateModel.application_id == application_id
            )
        )
        await session.commit()
