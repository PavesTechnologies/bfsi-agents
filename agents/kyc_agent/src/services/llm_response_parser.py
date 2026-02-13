"""
LLM Response Parser (Service)

Handles JSON parsing and validation.
"""

import json


def parse_llm_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON from LLM") from e
