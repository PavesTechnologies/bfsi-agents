"""
AUTO-GENERATED FILE.

Application entrypoint.
Used by uvicorn.
"""

import os
import sys
# Dynamically detect project root (bfsi-agents)
current_dir = os.path.abspath(os.path.dirname(__file__))

while current_dir != os.path.dirname(current_dir):
    if "vault" in os.listdir(current_dir):
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        break
    current_dir = os.path.dirname(current_dir)

print("Project root added to sys.path:", current_dir)

from src.app import create_app
from src.audit.mapper_event.register import register_audit_events
from src.core.config import get_settings

settings = get_settings()

app = create_app()
#  this line registers mapper events
register_audit_events()
