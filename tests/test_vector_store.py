from pathlib import Path

from app.rag.chunker import DocumentChunker
from app.rag.document_loader import KnowledgeBaseLoader
from app.rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


def build_test_store(tmp_path):
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)
    documents = loader.load()

    chunker = DocumentChunker(chunk_size=500, overlap=100)
    chunks = chunker.chunk_documents(documents)

    store = VectorStore(
        persist_directory=tmp_path / "chroma"
    )

    store.add_chunks(chunks)

    return store


def test_chunks_are_indexed(tmp_path):
    store = build_test_store(tmp_path)

    assert store.count() > 0


def test_relevant_chunks_can_be_retrieved(tmp_path):
    store = build_test_store(tmp_path)

    results = store.search(
        "What is the return policy?",
        top_k=5,
    )

    assert results
    assert any(
        "returns" in result["metadata"]["filename"].lower()
        for result in results
    )