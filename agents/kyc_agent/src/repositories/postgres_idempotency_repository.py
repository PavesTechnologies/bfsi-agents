from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from src.models.idempotency_key import IdempotencyKey

class PostgresIdempotencyRepository:
    def __init__(self, session):
        self.session = session

    def get_key(self, key: str) -> IdempotencyKey | None:
        stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def create_lock(self, key: str, payload_hash: str) -> bool:
        """
        Attempts to create a locked record for the key.
        Returns True if successful (acquired lock), False if key already exists.
        """
        try:
            record = IdempotencyKey(
                key=key,
                payload_hash=payload_hash,
                locked_at=datetime.utcnow()
            )
            self.session.add(record)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            return False

    def update_response(self, key: str, response_body: dict, status_code: int):
        stmt = (
            update(IdempotencyKey)
            .where(IdempotencyKey.key == key)
            .values(
                response_body=response_body,
                response_status=status_code,
                locked_at=None  # Unlock on completion
            )
        )
        self.session.execute(stmt)
        self.session.commit()

    def release_lock(self, key: str):
        """
        Removes the key record entirely if it was just a lock and hasn't completed.
        Used for cleanup on error.
        """
        # Only delete if it hasn't been completed (no response yet)
        stmt = (
            delete(IdempotencyKey)
            .where(IdempotencyKey.key == key)
            .where(IdempotencyKey.response_status.is_(None))
        )
        self.session.execute(stmt)
        self.session.commit()
