"""
STAGE 4b: Index chunks into Qdrant with dense + sparse vectors.

Two collections — RBI guidelines and bank policies — kept separate
because they have different update cadences, different access controls,
and the application can decide to query one or both.
"""

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PayloadSchemaType,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from config import DocumentSource, PipelineConfig
from pipeline.chunker import DocumentChunk
from pipeline.embedder import HybridEmbedder

logger = logging.getLogger(__name__)


class VectorIndexer:

    def __init__(self, config: PipelineConfig, embedder: HybridEmbedder):
        self.config = config
        self.embedder = embedder
        if not config.qdrant_url:
            raise RuntimeError("QDRANT_URL is not set — populate it via .env")
        self.client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key,
        )

    def create_collection(self, source: DocumentSource) -> None:
        """Create a collection with both dense and sparse vector slots."""
        coll_config = self.config.collections[source]

        self.client.recreate_collection(
            collection_name=coll_config.name,
            vectors_config={
                "dense": VectorParams(
                    size=coll_config.dense_dim,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(),
                ),
            },
        )

        for field_name, field_type in [
            ("chunk_type", PayloadSchemaType.KEYWORD),
            ("section_number", PayloadSchemaType.KEYWORD),
            ("chapter", PayloadSchemaType.KEYWORD),
            ("source_document", PayloadSchemaType.KEYWORD),
            ("product_types", PayloadSchemaType.KEYWORD),
            ("topic_tags", PayloadSchemaType.KEYWORD),
        ]:
            self.client.create_payload_index(
                collection_name=coll_config.name,
                field_name=field_name,
                field_schema=field_type,
            )

        logger.info("Created collection: %s", coll_config.name)

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        source: DocumentSource,
        batch_size: int = 64,
    ) -> None:
        """
        Embed and upsert chunks. The payload stores text_for_llm
        (what generation sees) plus all structural metadata.
        """
        if not chunks:
            logger.warning("No chunks to index for %s", source.value)
            return

        coll_name = self.config.collections[source].name

        all_texts = [c.text_for_embedding for c in chunks]
        self.embedder.build_idf(all_texts)

        points: list[PointStruct] = []
        for chunk in chunks:
            dense_vector = self.embedder.embed_passage(chunk.text_for_embedding)
            sparse = self.embedder.sparse_encode(chunk.text_for_embedding)

            point = PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
                vector={
                    "dense": dense_vector.tolist(),
                    "sparse": SparseVector(
                        indices=sparse["indices"],
                        values=sparse["values"],
                    ),
                },
                payload={
                    "text_for_llm": chunk.text_for_llm,
                    "text_for_embedding": chunk.text_for_embedding,

                    "chunk_type": chunk.chunk_type.value,
                    "breadcrumb": chunk.breadcrumb,
                    "section_number": chunk.section_number,
                    "section_title": chunk.section_title,
                    "chapter": chunk.chapter,
                    "parent_summary": chunk.parent_summary,

                    "source_document": chunk.source_document,
                    "page_numbers": chunk.page_numbers,

                    "raw_table_markdown": chunk.raw_table_markdown,
                    "raw_table_json": chunk.raw_table_json,

                    "product_types": chunk.product_types,
                    "topic_tags": chunk.topic_tags,
                    "effective_date": chunk.effective_date,
                },
            )
            points.append(point)

            if len(points) >= batch_size:
                self.client.upsert(collection_name=coll_name, points=points)
                logger.info("Upserted batch: %d points to %s", len(points), coll_name)
                points = []

        if points:
            self.client.upsert(collection_name=coll_name, points=points)

        logger.info("Indexing complete: %d chunks -> %s", len(chunks), coll_name)
