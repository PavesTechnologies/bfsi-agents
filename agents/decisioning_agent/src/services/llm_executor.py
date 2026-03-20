import logging
from typing import Any, Callable, Dict, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser

from src.core.config import get_settings
from src.services.model_loader import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()


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
                logger.warning("llm_attempt_returned_none", extra={"attempt": attempt})
                continue

            logger.info("llm_attempt_succeeded", extra={"attempt": attempt})
            return result

        except Exception as e:
            last_error = e
            logger.warning(
                "llm_attempt_failed",
                extra={"attempt": attempt, "error": str(e)},
            )

    if fallback_result is not None:
        logger.warning("llm_fallback_used")
        return fallback_result() if callable(fallback_result) else fallback_result

    raise RuntimeError(
        f"LLM execution failed after {attempts} retries"
    ) from last_error
