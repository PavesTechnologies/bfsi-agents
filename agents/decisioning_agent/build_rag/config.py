import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DocumentSource(Enum):
    RBI = "rbi_guidelines"
    BANK = "bank_policies"


class ChunkType(Enum):
    TEXT = "text"
    TABLE = "table"
    TABLE_NARRATION = "table_narration"
    LIST = "list"
    DEFINITION = "definition"


@dataclass
class CollectionConfig:
    name: str
    dense_dim: int = 1024
    sparse_enabled: bool = True


@dataclass
class PipelineConfig:
    embedding_model: str = "BAAI/bge-large-en-v1.5"

    max_chunk_tokens: int = 768
    min_chunk_tokens: int = 128
    chunk_overlap_tokens: int = 150

    # Qdrant Cloud — read from env so the key never lands in source.
    qdrant_url: str = field(
        default_factory=lambda: os.getenv("QDRANT_URL", "")
    )
    qdrant_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("QDRANT_API_KEY")
    )

    collections: dict = field(default_factory=lambda: {
        DocumentSource.RBI: CollectionConfig(name="rbi_guidelines"),
        DocumentSource.BANK: CollectionConfig(name="bank_policies"),
    })

    # Groq — OpenAI-compatible chat completions API.
    narration_model: str = "openai/gpt-oss-120b"
    groq_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY")
    )
