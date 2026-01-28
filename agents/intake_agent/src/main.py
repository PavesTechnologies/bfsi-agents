"""
AUTO-GENERATED FILE.

Application entrypoint.
Used by uvicorn.
"""

from src.app import create_app
from src.core.config import get_settings

settings = get_settings()

app = create_app()
