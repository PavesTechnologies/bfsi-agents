from sqlalchemy import select
from src.models.models import Address


class AddressDAO:

    def __init__(self, db):
        self.db = db

    async def get_primary_by_applicant_id(self, applicant_id):

        result = await self.db.execute(
            select(Address)
            .where(Address.applicant_id == applicant_id)
            .limit(1)
        )

        return result.scalar_one_or_none()
