from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.underwriting_human_review import UnderwritingHumanReview


class UnderwritingHumanReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_review(
        self,
        *,
        application_id: str,
        underwriting_decision_id: str | None,
        reviewer_id: str,
        decision: str,
        review_status: str,
        reason_keys: list[str],
        comments: str | None,
        review_packet: dict | None,
    ) -> UnderwritingHumanReview:
        review = UnderwritingHumanReview(
            application_id=application_id,
            underwriting_decision_id=underwriting_decision_id,
            reviewer_id=reviewer_id,
            decision=decision,
            review_status=review_status,
            reason_keys=reason_keys,
            comments=comments,
            review_packet=review_packet,
        )
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def get_latest_review(self, application_id: str) -> UnderwritingHumanReview | None:
        stmt = (
            select(UnderwritingHumanReview)
            .where(UnderwritingHumanReview.application_id == application_id)
            .order_by(UnderwritingHumanReview.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
