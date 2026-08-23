from pathlib import Path

from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore


PROJECT_ROOT = Path(__file__).resolve().parent

vector_store = VectorStore(
    persist_directory=PROJECT_ROOT / "chroma_db"
)

retriever = Retriever(
    vector_store=vector_store,
    top_k=5,
)

results = retriever.retrieve(
    "Can I return my shoes after 40 days?"
)

print(f"Found {len(results)} results\n")

for result in results:
    print("=" * 60)
    print("Document:", result["metadata"].get("document_id"))
    print("Status:", result["metadata"].get("status"))
    print("Authority:", result["metadata"].get("policy_authority"))
    print("Distance:", result["distance"])
    print("Content:", result["content"][:500])