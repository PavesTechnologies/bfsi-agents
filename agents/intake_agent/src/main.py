"""
AUTO-GENERATED FILE.

Application entrypoint.
Used by uvicorn.
"""

from src.app import create_app
<<<<<<< HEAD
from audit.mapper_event.register import register_audit_events
=======
from src.core.config import get_settings

settings = get_settings()
>>>>>>> 0f73d93e2650bc197bfff60b1383bd354353ec6f

app = create_app()
# 👇 this line registers mapper events
register_audit_events()
