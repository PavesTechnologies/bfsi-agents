import logging
import random
import time
from typing import Any, Callable, Dict, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser

from src.core.config import get_settings
from src.services.model_loader import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()

# Base wait seconds per attempt: attempt 0 → 8s, 1 → 16s, 2 → 32s + jitter ±3s
_BACKOFF_BASE = 8
_BACKOFF_JITTER = 3


def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "rate_limit" in msg or "429" in msg or "ratelimit" in msg


def execute_llm(
    *,
    prompt_template: str,
    inputs: Dict[str, Any],
    parser: Optional[BaseOutputParser] = None,
    temperature: float = 0.0,
    max_retries: Optional[int] = None,
    fallback_result: Optional[Callable[[], Any] | Any] = None,
) -> Any:

    llm = get_llm(temperature=temperature)

    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    if parser:
        chain = chain | parser

    last_error = None
    attempts = settings.llm_max_retries if max_retries is None else max_retries

    for attempt in range(attempts + 1):
        try:
            result = chain.invoke(inputs)

            if result is None:
                logger.warning("llm_attempt_returned_none (attempt=%d)", attempt)
                continue

            logger.info("llm_attempt_succeeded (attempt=%d)", attempt)
            return result

        except Exception as e:
            last_error = e

            if _is_rate_limit(e) and attempt < attempts:
                wait = (_BACKOFF_BASE * (2 ** attempt)) + random.uniform(0, _BACKOFF_JITTER)
                logger.warning(
                    "llm_rate_limit_backoff (attempt=%d): waiting %.1fs — %s",
                    attempt, wait, str(e)[:200],
                )
                time.sleep(wait)
            else:
                logger.warning(
                    "llm_attempt_failed (attempt=%d): %s: %s",
                    attempt, type(e).__name__, str(e)[:300],
                )

    if fallback_result is not None:
        logger.warning("llm_fallback_used")
        return fallback_result() if callable(fallback_result) else fallback_result

    raise RuntimeError(
        f"LLM execution failed after {attempts} retries"
    ) from last_error
