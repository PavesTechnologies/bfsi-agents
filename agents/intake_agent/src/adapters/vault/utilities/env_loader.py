import os

from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()


def load_env(key):
    """
    Returns the value for a given environment variable key.
    Raises an error if the key is missing or empty.
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value
