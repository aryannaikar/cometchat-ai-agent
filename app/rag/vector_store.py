from pathlib import Path

import chromadb

from app.rag.chunker import Chunk
from app.rag.embeddings import EmbeddingModel


class VectorStore:
    """ChromaDB-backed vector store for knowledge-base chunks."""

    def __init__(
        self,
        persist_directory: str | Path = "chroma_db",
        collection_name: str = "knowledge_base",
        embedding_model: EmbeddingModel | None = None,
    ):
        self.persist_directory = str(persist_directory)

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        self.embedding_model = (
            embedding_model or EmbeddingModel()
        )

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        embeddings = self.embedding_model.embed_documents(
            [chunk.content for chunk in chunks]
        )

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            embeddings=embeddings,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if not query.strip():
            return []

        query_embedding = self.embedding_model.embed_query(
            query
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        return [
            {
                "chunk_id": chunk_id,
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
            for chunk_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
            )
        ]

    def count(self) -> int:
        return self.collection.count()