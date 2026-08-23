from pathlib import Path

from app.rag.indexer import KnowledgeBaseIndexer
from app.rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


vector_store = VectorStore(
    persist_directory=PROJECT_ROOT / "chroma_db"
)

indexer = KnowledgeBaseIndexer(
    knowledge_base_path=KNOWLEDGE_BASE,
    vector_store=vector_store,
)

count = indexer.index()

print(f"Indexed {count} chunks.")