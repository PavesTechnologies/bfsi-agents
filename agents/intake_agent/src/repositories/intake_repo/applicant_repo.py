from sqlalchemy import select
from src.models.models import Applicant


class ApplicantDAO:

    def __init__(self, db):
        self.db = db

    async def get_primary_by_application_id(self, application_id):

        result = await self.db.execute(
            select(Applicant)
            .where(Applicant.application_id == application_id)
            .limit(1)
        )

        return result.scalar_one_or_none()
