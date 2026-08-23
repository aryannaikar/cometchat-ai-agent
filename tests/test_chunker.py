from pathlib import Path

from app.rag.chunker import DocumentChunker
from app.rag.document_loader import KnowledgeBaseLoader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


def test_documents_are_split_into_chunks():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)
    documents = loader.load()

    chunker = DocumentChunker(chunk_size=500, overlap=100)
    chunks = chunker.chunk_documents(documents)

    assert len(chunks) > len(documents)


def test_chunks_preserve_document_identity():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)
    documents = loader.load()

    chunker = DocumentChunker(chunk_size=500, overlap=100)
    chunks = chunker.chunk_documents(documents)

    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.document_id
        assert chunk.content
        assert chunk.metadata["document_id"] == chunk.document_id
        assert chunk.metadata["chunk_id"] == chunk.chunk_id


def test_chunks_preserve_authority_metadata():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)
    documents = loader.load()

    current = next(
        document
        for document in documents
        if document.filename == "01-returns-policy-current.md"
    )

    chunker = DocumentChunker(
        chunk_size=500,
        overlap=100,
    )

    chunks = chunker.chunk_document(current)

    assert chunks

    for chunk in chunks:
        assert chunk.metadata["status"] == "active"
        assert chunk.metadata["policy_authority"] == "official"
        assert chunk.metadata["audience"] == "customer"
        assert chunk.metadata["document_id"] == current.document_id