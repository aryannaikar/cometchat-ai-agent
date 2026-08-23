from pathlib import Path

from app.rag.document_loader import KnowledgeBaseLoader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


def test_loads_all_knowledge_base_documents():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)

    documents = loader.load()

    assert len(documents) == 14


def test_documents_preserve_provenance():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)

    documents = loader.load()

    first = documents[0]

    assert first.document_id
    assert first.filename.endswith(".md")
    assert first.path
    assert first.title
    assert first.content

    assert first.metadata["document_id"] == first.document_id
    assert first.metadata["filename"] == first.filename


def test_frontmatter_is_preserved():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)

    documents = loader.load()

    current = next(
        document
        for document in documents
        if document.filename == "01-returns-policy-current.md"
    )

    assert current.metadata["status"] == "active"
    assert current.metadata["policy_authority"] == "official"
    assert current.metadata["audience"] == "customer"


def test_legacy_policy_metadata_is_preserved():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)

    documents = loader.load()

    legacy = next(
        document
        for document in documents
        if document.filename == "02-returns-policy-legacy.md"
    )

    assert legacy.metadata["status"] == "superseded"
    assert legacy.metadata["policy_authority"] == "official"
    assert legacy.metadata["superseded_by"] == "RET-2026-01"


def test_internal_migration_metadata_is_preserved():
    loader = KnowledgeBaseLoader(KNOWLEDGE_BASE)

    documents = loader.load()

    migration = next(
        document
        for document in documents
        if document.filename == "14-internal-content-migration-notes.md"
    )

    assert migration.metadata["status"] == "draft"
    assert migration.metadata["audience"] == "internal"
    assert migration.metadata["policy_authority"] is None
    assert migration.metadata["customer_answering"] is False