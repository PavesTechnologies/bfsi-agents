"""
Evidence Repository

Stores evidence file paths and metadata.
Repository layer - persistence only, no business logic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime


class EvidenceFileNotFoundError(Exception):
    """Raised when evidence file is not found."""

    def __init__(self, evidence_id: str, path: str):
        self.evidence_id = evidence_id
        self.path = path
        super().__init__(
            f"Evidence file not found: {evidence_id} at {path}"
        )


class EvidenceRepository:
    """
    Repository for persisting evidence paths and metadata.
    
    In production, this would interact with a database or object store.
    For now, this is an abstract interface that tests can mock.
    """

    async def store_evidence_path(
        self,
        application_id: str,
        evidence_id: str,
        evidence_type: str,
        path: str,
        source: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        rule_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store evidence path in repository.

        Args:
            application_id: Application ID
            evidence_id: Unique evidence identifier
            evidence_type: Type of evidence (validation, enrichment, etc.)
            path: Path to evidence file
            source: Source name (validator, adapter, etc.)
            entity_type: Optional entity type (applicant, address, etc.)
            entity_id: Optional entity ID
            rule_id: Optional rule ID

        Returns:
            dict: Stored evidence record

        Raises:
            RepositoryError: If storing fails
        """
        raise NotImplementedError(
            "Subclass must implement store_evidence_path"
        )

    async def get_evidence_by_application(
        self,
        application_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all evidence paths for an application.

        Args:
            application_id: Application ID

        Returns:
            list: Evidence records for the application

        Raises:
            RepositoryError: If retrieval fails
        """
        raise NotImplementedError(
            "Subclass must implement get_evidence_by_application"
        )

    async def get_evidence_by_id(
        self,
        evidence_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve evidence by ID.

        Args:
            evidence_id: Unique evidence identifier

        Returns:
            dict: Evidence record, or None if not found

        Raises:
            RepositoryError: If retrieval fails
        """
        raise NotImplementedError(
            "Subclass must implement get_evidence_by_id"
        )

    async def delete_evidence(
        self,
        evidence_id: str,
    ) -> bool:
        """
        Delete evidence by ID.

        Args:
            evidence_id: Unique evidence identifier

        Returns:
            bool: True if deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        raise NotImplementedError(
            "Subclass must implement delete_evidence"
        )


class InMemoryEvidenceRepository(EvidenceRepository):
    """
    In-memory evidence repository for testing.
    
    This is NOT for production use - it's a reference implementation.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: Dict[str, Dict[str, Any]] = {}

    async def store_evidence_path(
        self,
        application_id: str,
        evidence_id: str,
        evidence_type: str,
        path: str,
        source: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        rule_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store evidence in memory."""
        record = {
            "id": evidence_id,
            "application_id": application_id,
            "type": evidence_type,
            "path": path,
            "source": source,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "rule_id": rule_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        self._storage[evidence_id] = record
        return record

    async def get_evidence_by_application(
        self,
        application_id: str,
    ) -> List[Dict[str, Any]]:
        """Retrieve evidence by application ID."""
        return [
            record
            for record in self._storage.values()
            if record["application_id"] == application_id
        ]

    async def get_evidence_by_id(
        self,
        evidence_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve evidence by ID."""
        return self._storage.get(evidence_id)

    async def delete_evidence(
        self,
        evidence_id: str,
    ) -> bool:
        """Delete evidence by ID."""
        if evidence_id in self._storage:
            del self._storage[evidence_id]
            return True
        return False
