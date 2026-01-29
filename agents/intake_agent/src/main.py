"""
AUTO-GENERATED FILE.

Application entrypoint.
Used by uvicorn.
"""

from src.app import create_app
from src.audit.mapper_event.register import register_audit_events
from src.core.config import get_settings
import src.audit.mapper_event.audit_guard
settings = get_settings()

app = create_app()
#  this line registers mapper events
register_audit_events()
