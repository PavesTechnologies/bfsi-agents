"""
Master orchestrator for the document embedding pipeline.

Drop PDFs into the bundled folders and run with no args:
    poetry run python ingest.py

Or override the directories explicitly:
    poetry run python ingest.py --rbi-dir ./rbi_guidelines --bank-dir ./bank_policies
"""

import argparse
import logging
import os
from pathlib import Path

# Default doc directories — co-located with this script.
BUILD_RAG_ROOT = Path(__file__).parent
DEFAULT_RBI_DIR = BUILD_RAG_ROOT / "rbi_guidelines"
DEFAULT_BANK_DIR = BUILD_RAG_ROOT / "bank_policies"

from dotenv import load_dotenv
from groq import Groq

from config import DocumentSource, PipelineConfig
from pipeline.chunker import chunk_document
from pipeline.embedder import HybridEmbedder
from pipeline.indexer import VectorIndexer
from pipeline.parser import parse_document
from pipeline.structure import build_section_tree, flatten_with_context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def ingest_documents(
    rbi_dir: str,
    bank_dir: str,
    config: PipelineConfig | None = None,
) -> None:
    config = config or PipelineConfig()

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set — populate it via .env")

    groq_client = Groq()  # picks up GROQ_API_KEY from env
    embedder = HybridEmbedder(config.embedding_model)
    indexer = VectorIndexer(config, embedder)

    indexer.create_collection(DocumentSource.RBI)
    indexer.create_collection(DocumentSource.BANK)

    for source, directory in [
        (DocumentSource.RBI, rbi_dir),
        (DocumentSource.BANK, bank_dir),
    ]:
        all_chunks = []
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.warning("Directory does not exist, skipping: %s", directory_path)
            continue

        doc_paths = sorted(
            p for p in directory_path.glob("**/*")
            if p.is_file() and p.suffix.lower() in {".pdf", ".docx"}
        )

        for file_path in doc_paths:
            logger.info("Processing: %s", file_path.name)

            elements = parse_document(str(file_path))
            section_tree = build_section_tree(elements)
            contextualized = flatten_with_context(section_tree)

            chunks = chunk_document(
                contextualized_elements=contextualized,
                source_document=file_path.stem,
                document_source=source.value,
                config=config,
                groq_client=groq_client,
            )

            all_chunks.extend(chunks)
            table_count = sum(
                1 for c in chunks if c.chunk_type.value == "table_narration"
            )
            logger.info("  -> %d chunks (%d tables)", len(chunks), table_count)

        indexer.index_chunks(all_chunks, source)
        logger.info("Done %s: %d total chunks indexed", source.value, len(all_chunks))


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest regulatory + bank policy PDFs")
    parser.add_argument(
        "--rbi-dir",
        default=str(DEFAULT_RBI_DIR),
        help=f"Directory of RBI PDFs (default: {DEFAULT_RBI_DIR})",
    )
    parser.add_argument(
        "--bank-dir",
        default=str(DEFAULT_BANK_DIR),
        help=f"Directory of bank policy PDFs (default: {DEFAULT_BANK_DIR})",
    )
    args = parser.parse_args()

    ingest_documents(args.rbi_dir, args.bank_dir)


if __name__ == "__main__":
    main()
