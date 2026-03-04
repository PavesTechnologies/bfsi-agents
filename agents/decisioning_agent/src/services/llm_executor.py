from typing import Any, Dict, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser

from src.services.model_loader import get_llm


def execute_llm(
    *,
    prompt_template: str,
    inputs: Dict[str, Any],
    parser: Optional[BaseOutputParser] = None,
    temperature: float = 0.0,
    max_retries: int = 2,
) -> Any:

    llm = get_llm(temperature=temperature)

    prompt = PromptTemplate.from_template(prompt_template)

    chain = prompt | llm

    if parser:
        chain = chain | parser

    last_error = None

    for attempt in range(max_retries + 1):

        try:
            result = chain.invoke(inputs)

            print(f"LLM attempt {attempt}")

            if result is None:
                continue

            # # If confidence exists check it
            # if hasattr(result, "confidence_score"):
            #     if result.confidence_score < 0.75:
            #         continue
            
            return result

        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"LLM execution failed after {max_retries} retries"
    ) from last_error