"""Runtime version metadata for underwriting decisions."""

from src.core.config import get_settings


PROMPT_VERSION = "deterministic-underwriting-v1"


def get_runtime_versions() -> dict:
    settings = get_settings()
    return {
        "model_version": settings.llm_model,
        "prompt_version": PROMPT_VERSION,
    }
