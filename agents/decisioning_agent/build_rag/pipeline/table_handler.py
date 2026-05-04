"""
Table handling: dual representation per table.

Embedding raw HTML/markdown of a table retrieves poorly — embedding
models are trained on prose. So we narrate every table into natural
language for embedding, and keep the structured form as metadata so
the LLM still sees the precise values at generation time.

Narration uses Groq (OpenAI-compatible chat completions) so we get
fast, cheap inference for the bulk-narration step.
"""

import json
import logging
from typing import Optional

from groq import Groq

from config import PipelineConfig

logger = logging.getLogger(__name__)


def narrate_table(
    table_data: Optional[list[dict]],
    table_html: Optional[str],
    section_context: str,
    client: Groq,
    model: str = PipelineConfig().narration_model,
) -> str:
    """
    Convert a table into self-contained natural language prose.

    Returns a string that mentions every data point, the column meaning,
    and the section context — so the embedding alone is enough to be
    retrieved by a query like "LTV cap for 50 lakh loan".
    """
    prompt = f"""You are a regulatory document analyst. Convert this table
into a clear, complete natural language description.

RULES:
- Include EVERY data point from the table — omit nothing
- Use the exact numbers, percentages, and terms from the table
- Mention what each column represents
- Write it as flowing prose, not a list
- Include the section context so the narration is self-contained
- Keep it concise but complete

SECTION CONTEXT: {section_context}

TABLE (HTML):
{table_html or "Not available"}

TABLE (structured):
{json.dumps(table_data, indent=2) if table_data else "Not available"}

Write the natural language narration:"""

    response = client.chat.completions.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content or ""


def table_to_markdown(table_data: Optional[list[dict]]) -> str:
    """Render structured table data as markdown for the LLM-side payload."""
    if not table_data:
        return ""

    headers = list(table_data[0].keys())

    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for row in table_data:
        md += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

    return md
