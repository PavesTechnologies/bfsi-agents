from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from src.models.langgraph_failed_threads import DecisioningFailedThread


class DecisioningFailedThreadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ----------------------------------------
    # 🔍 Get failed thread (for resume)
    # ----------------------------------------
    async def get_failed_thread(self, application_id: str) -> DecisioningFailedThread | None:
        result = await self.session.execute(
            select(DecisioningFailedThread).where(
                DecisioningFailedThread.application_id == application_id
            )
        )
        return result.scalar_one_or_none()

    # ----------------------------------------
    # 💾 Save or Update failure
    # ----------------------------------------
    async def save_failure(
        self,
        application_id: str,
        thread_id: str,
        failed_node: str | None = None,
        error_message: str | None = None
    ):
        existing = await self.get_failed_thread(application_id)

        if existing:
            existing.thread_id = thread_id
            existing.failed_node = failed_node
            existing.error_message = error_message
            existing.retry_count += 1
        else:
            record = DecisioningFailedThread(
                application_id=application_id,
                thread_id=thread_id,
                failed_node=failed_node,
                error_message=error_message,
                retry_count=0
            )
            self.session.add(record)

        await self.session.commit()

    # ----------------------------------------
    # ❌ Delete after success
    # ----------------------------------------
    async def delete_failed_thread(self, application_id: str):
        await self.session.execute(
            delete(DecisioningFailedThread).where(
                DecisioningFailedThread.application_id == application_id
            )
        )
        await self.session.commit()

    # ----------------------------------------
    # 🔁 Increment retry (optional use)
    # ----------------------------------------
    async def increment_retry(self, application_id: str):
        await self.session.execute(
            update(DecisioningFailedThread)
            .where(DecisioningFailedThread.application_id == application_id)
            .values(retry_count=DecisioningFailedThread.retry_count + 1)
        )
        await self.session.commit()