"""
STAGE 3: Content-aware chunking.

Tables become exactly one chunk each (narration embedded, raw kept as
metadata). Text gets semantic splitting on sentence boundaries inside
each section, with token-level overlap. Section context is prepended
to every chunk so meaning survives in isolation.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import tiktoken
from groq import Groq

from config import ChunkType, PipelineConfig
from pipeline.table_handler import narrate_table, table_to_markdown


@dataclass
class DocumentChunk:
    chunk_id: str

    text_for_embedding: str
    text_for_llm: str

    chunk_type: ChunkType

    breadcrumb: str
    section_number: str
    section_title: str
    chapter: str
    parent_summary: str

    source_document: str
    page_numbers: list[int] = field(default_factory=list)

    raw_table_markdown: Optional[str] = None
    raw_table_json: Optional[list] = None

    product_types: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    effective_date: Optional[str] = None


def chunk_document(
    contextualized_elements: list[dict],
    source_document: str,
    document_source: str,
    config: PipelineConfig,
    groq_client: Groq,
) -> list[DocumentChunk]:
    """Run the contextualized element list through type-aware chunking."""
    tokenizer = tiktoken.get_encoding("cl100k_base")
    chunks: list[DocumentChunk] = []
    chunk_counter = 0
    text_buffer: list[dict] = []

    for ctx_elem in contextualized_elements:
        elem = ctx_elem["element"]

        if elem.element_type == "Table":
            if text_buffer:
                text_chunks = _semantic_chunk_text(
                    text_buffer, config, tokenizer, source_document, chunk_counter
                )
                chunks.extend(text_chunks)
                chunk_counter += len(text_chunks)
                text_buffer = []

            table_chunk = _create_table_chunk(
                elem, ctx_elem, source_document, chunk_counter,
                config, groq_client,
            )
            chunks.append(table_chunk)
            chunk_counter += 1

        else:
            text_buffer.append(ctx_elem)

    if text_buffer:
        text_chunks = _semantic_chunk_text(
            text_buffer, config, tokenizer, source_document, chunk_counter
        )
        chunks.extend(text_chunks)

    return chunks


def _create_table_chunk(
    elem,
    ctx_elem: dict,
    source_doc: str,
    counter: int,
    config: PipelineConfig,
    client: Groq,
) -> DocumentChunk:
    """
    Build the dual-representation table chunk.

    text_for_embedding -> narration only (retrieves well).
    text_for_llm      -> narration + raw markdown (precise values).
    raw_table_json    -> original structured rows (for programmatic use).
    """
    narration = narrate_table(
        table_data=elem.table_data,
        table_html=elem.table_html,
        section_context=ctx_elem["breadcrumb"],
        client=client,
        model=config.narration_model,
    )

    raw_markdown = table_to_markdown(elem.table_data)

    llm_text = (
        f"[Section: {ctx_elem['breadcrumb']}]\n\n"
        f"{narration}\n\n"
        f"Original Table:\n{raw_markdown}"
    )

    embedding_text = f"{ctx_elem['section_title']}. {narration}"

    return DocumentChunk(
        chunk_id=f"{source_doc}_chunk_{counter}",
        text_for_embedding=embedding_text,
        text_for_llm=llm_text,
        chunk_type=ChunkType.TABLE_NARRATION,
        breadcrumb=ctx_elem["breadcrumb"],
        section_number=ctx_elem.get("section_number") or "",
        section_title=ctx_elem["section_title"],
        chapter=ctx_elem["chapter"],
        parent_summary=ctx_elem.get("parent_summary", ""),
        source_document=source_doc,
        page_numbers=[elem.page_number],
        raw_table_markdown=raw_markdown,
        raw_table_json=elem.table_data,
    )


def _semantic_chunk_text(
    text_elements: list[dict],
    config: PipelineConfig,
    tokenizer,
    source_doc: str,
    start_counter: int,
) -> list[DocumentChunk]:
    """
    Group elements by section, split into sentences, and pack into
    chunks bounded by max_chunk_tokens with chunk_overlap_tokens of
    sentence-level overlap between adjacent chunks.
    """
    chunks: list[DocumentChunk] = []
    counter = start_counter

    section_groups: dict[str, list[dict]] = {}
    for ctx_elem in text_elements:
        section_key = ctx_elem.get("section_number") or ctx_elem.get("section_title", "unknown")
        section_groups.setdefault(section_key, []).append(ctx_elem)

    for elements in section_groups.values():
        section_text = " ".join(e["element"].text for e in elements)
        section_ctx = elements[0]
        page_numbers = sorted({e["element"].page_number for e in elements})

        sentences = _split_sentences(section_text)

        current_sentences: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(tokenizer.encode(sentence))

            if current_tokens + sentence_tokens > config.max_chunk_tokens and current_sentences:
                chunks.append(_emit_text_chunk(
                    current_sentences, section_ctx, source_doc, counter, page_numbers,
                ))
                counter += 1

                # Carry overlap from the tail of the just-emitted chunk.
                overlap_tokens = 0
                overlap_start = len(current_sentences)
                for i in range(len(current_sentences) - 1, -1, -1):
                    t = len(tokenizer.encode(current_sentences[i]))
                    if overlap_tokens + t > config.chunk_overlap_tokens:
                        break
                    overlap_tokens += t
                    overlap_start = i

                current_sentences = current_sentences[overlap_start:]
                current_tokens = overlap_tokens

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            if len(tokenizer.encode(chunk_text)) >= config.min_chunk_tokens:
                chunks.append(_emit_text_chunk(
                    current_sentences, section_ctx, source_doc, counter, page_numbers,
                ))
                counter += 1

    return chunks


def _emit_text_chunk(
    sentences: list[str],
    section_ctx: dict,
    source_doc: str,
    counter: int,
    page_numbers: list[int],
) -> DocumentChunk:
    chunk_text = " ".join(sentences)

    return DocumentChunk(
        chunk_id=f"{source_doc}_chunk_{counter}",
        text_for_embedding=f"{section_ctx['section_title']}. {chunk_text}",
        text_for_llm=f"[Section: {section_ctx['breadcrumb']}]\n\n{chunk_text}",
        chunk_type=ChunkType.TEXT,
        breadcrumb=section_ctx["breadcrumb"],
        section_number=section_ctx.get("section_number") or "",
        section_title=section_ctx["section_title"],
        chapter=section_ctx["chapter"],
        parent_summary=section_ctx.get("parent_summary", ""),
        source_document=source_doc,
        page_numbers=page_numbers,
    )


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]
