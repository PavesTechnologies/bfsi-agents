"""
Background RAG ingestion worker.
Called via FastAPI BackgroundTasks after a document is uploaded.

Pipeline:
  1. Load PDF from storage_path (local or S3)
  2. Parse pages with pypdf
  3. Chunk text (768 tokens max, 150 overlap)
  4. Embed chunks with sentence-transformers BAAI/bge-large-en-v1.5
  5. Upsert into Qdrant collection
  6. Update RagDocument + RagIngestionJob status
  7. If replacing an old document, delete its Qdrant points
"""
import uuid
import logging
import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

from src.models.rag_document import RagDocument, RagIngestionJob
from src.core.config import get_settings
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

CHUNK_SIZE = 768
CHUNK_OVERLAP = 150
VECTOR_DIM = 1024  # bge-large-en-v1.5


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def _load_pdf_text(storage_path: str) -> list[tuple[int, str]]:
    """Returns list of (page_number, page_text)."""
    from pypdf import PdfReader
    if storage_path.startswith("s3://"):
        import boto3, tempfile
        parts = storage_path[5:].split("/", 1)
        bucket, key = parts[0], parts[1]
        s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION)
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        s3.download_fileobj(bucket, key, tmp)
        tmp.close()
        path = tmp.name
    else:
        path = storage_path

    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append((i + 1, text))
    return pages


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _embed_chunks(chunks: list[str]) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(settings.RAG_EMBEDDING_MODEL)
    embeddings = model.encode(chunks, batch_size=32, normalize_embeddings=True)
    return embeddings.tolist()


def _ensure_collection(client: QdrantClient, collection_name: str) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )


async def run_ingestion(document_id: str) -> None:
    """Entry point called by BackgroundTasks."""
    async with AsyncSessionLocal() as db:
        doc_result = await db.execute(select(RagDocument).where(RagDocument.id == uuid.UUID(document_id)))
        doc = doc_result.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {document_id} not found for ingestion")
            return

        job_result = await db.execute(
            select(RagIngestionJob)
            .where(RagIngestionJob.document_id == doc.id)
            .order_by(RagIngestionJob.created_at.desc())
        )
        job = job_result.scalars().first()
        if not job:
            logger.error(f"No ingestion job found for document {document_id}")
            return

        job.status = "RUNNING"
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        doc.status = "PROCESSING"
        await db.commit()

        try:
            logger.info(f"Starting ingestion for document {document_id} → {doc.collection_name}")

            pages = _load_pdf_text(doc.storage_path)
            all_chunks: list[str] = []
            chunk_meta: list[dict] = []

            for page_num, page_text in pages:
                chunks = _chunk_text(page_text)
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    chunk_meta.append({"page": page_num, "chunk_index": i, "document_name": doc.document_name})

            job.progress_pct = 20
            await db.commit()

            embeddings = _embed_chunks(all_chunks)
            job.progress_pct = 60
            await db.commit()

            client = _get_qdrant_client()
            _ensure_collection(client, doc.collection_name)

            point_ids = []
            points = []
            for i, (embedding, meta, text) in enumerate(zip(embeddings, chunk_meta, all_chunks)):
                pid = str(uuid.uuid4())
                point_ids.append(pid)
                points.append(PointStruct(
                    id=pid,
                    vector=embedding,
                    payload={**meta, "text": text, "document_id": str(doc.id)},
                ))

            batch_size = 100
            for i in range(0, len(points), batch_size):
                client.upsert(collection_name=doc.collection_name, points=points[i:i + batch_size])

            job.progress_pct = 90
            await db.commit()

            # Delete old document's vectors if replacing
            if doc.replaced_document_id:
                old_result = await db.execute(select(RagDocument).where(RagDocument.id == doc.replaced_document_id))
                old_doc = old_result.scalar_one_or_none()
                if old_doc and old_doc.qdrant_point_ids:
                    client.delete(collection_name=doc.collection_name, points_selector=old_doc.qdrant_point_ids)
                if old_doc:
                    old_doc.status = "REPLACED"

            doc.status = "ACTIVE"
            doc.qdrant_point_ids = point_ids
            doc.chunk_count = len(all_chunks)
            doc.updated_at = datetime.datetime.now(datetime.timezone.utc)

            job.status = "COMPLETED"
            job.progress_pct = 100
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)

            logger.info(f"Ingestion complete: {len(all_chunks)} chunks → {doc.collection_name}")

        except Exception as e:
            logger.exception(f"Ingestion failed for document {document_id}: {e}")
            doc.status = "FAILED"
            job.status = "FAILED"
            job.error_message = str(e)

        await db.commit()
