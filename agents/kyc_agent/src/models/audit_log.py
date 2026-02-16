from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, DateTime, ForeignKey, text, String, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.utils.migration_database import Base
from .enums import ActorType

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = mapped_column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    entity_type = mapped_column(String(100))
    entity_id = mapped_column(UUID)

    action = mapped_column(String(100))

    actor_type = mapped_column(
        Enum(ActorType, name="actor_type_enum"),
        nullable=False,
    )

    actor_id = mapped_column(UUID, nullable=True)

    audit_metadata = mapped_column(JSONB)  # ✅ renamed

    timestamp = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()")
    )