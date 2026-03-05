"""
Repository for request metadata persistence

Handles storing and retrieving request metadata from the database
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import logging

from src.models.metadata import RequestMetadataRecord, RequestMetadata

logger = logging.getLogger(__name__)


class MetadataRepository:
    """Repository for managing request metadata records"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        request_id: UUID,
        app_id: UUID,
        metadata: RequestMetadata,
    ) -> RequestMetadataRecord:
        """
        Create and persist request metadata record.

        Args:
            request_id: Unique request identifier
            app_id: Application identifier
            metadata: Parsed request metadata

        Returns:
            Persisted RequestMetadataRecord

        Raises:
            IntegrityError: If request_id already exists
        """
        # Use pydantic model dump for JSON storage to avoid str() calls
        metadata_json = metadata.model_dump()

        record = RequestMetadataRecord(
            request_id=request_id,
            app_id=app_id,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
            browser=metadata.browser,
            os=metadata.os,
            device_type=metadata.device_type,
            accept_language=metadata.accept_language,
            referrer=metadata.referrer,
            metadata_json=metadata_json,
        )

        self.db.add(record)

        try:
            await self.db.flush()
        except IntegrityError:
            logger.warning(
                "Metadata for request already exists",
                extra={"request_id": str(request_id)},
            )
            raise

        logger.info(
            "Stored metadata for request",
            extra={
                "request_id": str(request_id),
                "ip_address": metadata.ip_address,
                "device_type": metadata.device_type,
            },
        )

        return record

    async def get_by_request_id(self, request_id: UUID) -> RequestMetadataRecord | None:
        """
        Retrieve metadata by request ID.

        Args:
            request_id: Request identifier

        Returns:
            RequestMetadataRecord or None if not found
        """
        result = await self.db.execute(
            select(RequestMetadataRecord).where(
                RequestMetadataRecord.request_id == request_id
            )
        )
        return result.scalars().first()

    async def get_by_app_id(self, app_id: UUID, limit: int = 100) -> list[RequestMetadataRecord]:
        """
        Retrieve metadata records for an application.

        Args:
            app_id: Application identifier
            limit: Maximum number of records to return

        Returns:
            List of RequestMetadataRecord objects
        """
        result = await self.db.execute(
            select(RequestMetadataRecord)
            .where(RequestMetadataRecord.app_id == app_id)
            .order_by(RequestMetadataRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_ip_address(self, ip_address: str, limit: int = 100) -> list[RequestMetadataRecord]:
        """
        Retrieve metadata records by IP address.

        Useful for detecting abusive patterns or user behavior analysis.

        Args:
            ip_address: Client IP address
            limit: Maximum number of records to return

        Returns:
            List of RequestMetadataRecord objects
        """
        result = await self.db.execute(
            select(RequestMetadataRecord)
            .where(RequestMetadataRecord.ip_address == ip_address)
            .order_by(RequestMetadataRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_device_type(
        self,
        app_id: UUID,
        device_type: str,
        limit: int = 100,
    ) -> list[RequestMetadataRecord]:
        """
        Retrieve metadata records filtered by device type.

        Args:
            app_id: Application identifier
            device_type: Device type filter (mobile, tablet, desktop)
            limit: Maximum number of records to return

        Returns:
            List of RequestMetadataRecord objects
        """
        result = await self.db.execute(
            select(RequestMetadataRecord)
            .where(
                (RequestMetadataRecord.app_id == app_id)
                & (RequestMetadataRecord.device_type == device_type)
            )
            .order_by(RequestMetadataRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
