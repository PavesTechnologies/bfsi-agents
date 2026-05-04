"""
Singleton clients for the RAG retrieval pipeline.

BGE encoder is large (~1.3GB) — loaded once at module import and reused.
Qdrant client multiplexes a single HTTP connection.
"""

import logging
import os
import threading
from typing import Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")

# BGE convention: query passages get a different prefix than indexed passages.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

RBI_COLLECTION = "rbi_guidelines"
BANK_COLLECTION = "bank_policies"


_embedder_lock = threading.Lock()
_embedder: Optional[SentenceTransformer] = None

_qdrant_lock = threading.Lock()
_qdrant: Optional[QdrantClient] = None


def get_embedder() -> SentenceTransformer:
    """Return the shared BGE SentenceTransformer (lazy-loaded, thread-safe)."""
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                logger.info("Loading BGE embedder: %s", EMBEDDING_MODEL)
                _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def get_qdrant() -> QdrantClient:
    """Return the shared Qdrant client (cloud cluster, lazy-loaded)."""
    global _qdrant
    if _qdrant is None:
        with _qdrant_lock:
            if _qdrant is None:
                url = os.getenv("QDRANT_URL")
                api_key = os.getenv("QDRANT_API_KEY")
                if not url:
                    raise RuntimeError(
                        "QDRANT_URL is not set — RAG retrieval cannot run. "
                        "Populate it via the decisioning_agent .env."
                    )
                logger.info("Connecting to Qdrant: %s", url)
                _qdrant = QdrantClient(url=url, api_key=api_key)
    return _qdrant


def embed_query(text: str) -> list[float]:
    """Encode a search query with the BGE query prefix and L2-normalize."""
    embedder = get_embedder()
    vector = embedder.encode(QUERY_PREFIX + text, normalize_embeddings=True)
    return vector.tolist()
