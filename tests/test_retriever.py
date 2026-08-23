from pathlib import Path
from app.rag.chunker import DocumentChunker
from app.rag.document_loader import KnowledgeBaseLoader
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


def build_retriever(tmp_path):
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)
    documents = loader.load()

    chunker = DocumentChunker(
        chunk_size=500,
        overlap=100,
    )

    chunks = chunker.chunk_documents(documents)

    store = VectorStore(
        persist_directory=tmp_path / "chroma"
    )

    store.add_chunks(chunks)

    return Retriever(store, top_k=5)


def test_retriever_returns_evidence(tmp_path):
    retriever = build_retriever(tmp_path)

    results = retriever.retrieve(
        "Can I return an item after 45 days?"
    )

    assert results

    filenames = [
        result["metadata"]["filename"]
        for result in results
    ]

    assert any(
        "returns-policy" in filename
        for filename in filenames
    )