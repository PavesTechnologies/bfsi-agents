"""
AUTO-GENERATED FILE.

Application entrypoint.
Used by uvicorn.
"""

#from src.app import create_app
from agents.intake_agent.src.app import create_app

app = create_app()
