from dotenv import load_dotenv
from pathlib import Path
import os

# Resolve path to agents/intake_agent/.env
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(f"DATABASE_URL not set. Expected in {ENV_PATH}")
