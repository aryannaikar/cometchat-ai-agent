from pathlib import Path

from app.rag.chunker import DocumentChunker
from app.rag.document_loader import KnowledgeBaseLoader
from app.rag.vector_store import VectorStore


class KnowledgeBaseIndexer:
    """Loads, chunks, and indexes the knowledge base."""

    def __init__(
        self,
        knowledge_base_path: str | Path,
        vector_store: VectorStore,
        chunker: DocumentChunker | None = None,
    ):
        self.loader = KnowledgeBaseLoader(knowledge_base_path)
        self.vector_store = vector_store
        self.chunker = chunker or DocumentChunker()

    def index(self) -> int:
        documents = self.loader.load()

        chunks = self.chunker.chunk_documents(documents)

        self.vector_store.add_chunks(chunks)

        return len(chunks)