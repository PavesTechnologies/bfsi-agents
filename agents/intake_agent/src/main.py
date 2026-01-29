"""
AUTO-GENERATED FILE.

Application entrypoint.
Used by uvicorn.
"""

from src.app import create_app
from audit.mapper_event.register import register_audit_events

app = create_app()
# 👇 this line registers mapper events
register_audit_events()
