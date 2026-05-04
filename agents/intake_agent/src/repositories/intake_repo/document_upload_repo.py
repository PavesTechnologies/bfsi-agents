from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import PgsqlDocument


class LoanIntakeDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(self, data: dict) -> PgsqlDocument:
        document = PgsqlDocument(**data)
        self.db.add(document)
        return document

    async def get_uploaded_document_types(self, application_id) -> set[str]:
        """Return the set of distinct document_type values uploaded for this application."""
        result = await self.db.execute(
            select(PgsqlDocument.document_type).where(
                PgsqlDocument.application_id == application_id
            )
        )
        return {row[0] for row in result.fetchall()}
