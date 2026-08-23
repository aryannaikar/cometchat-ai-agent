from app.agent.agent import AIAgent


class FakeRetriever:
    """Returns controlled evidence for an end-to-end pipeline test."""

    def retrieve(self, query: str) -> list[dict]:
        return [
            {
                "metadata": {
                    "document_id": "RET-2026-01",
                    "filename": "return-policy-current.md",
                    "status": "active",
                    "policy_authority": "official",
                    "audience": "customer",
                },
                "content": (
                    "Customers may return items within "
                    "30 calendar days."
                ),
            },
            {
                "metadata": {
                    "document_id": "RET-2024-01",
                    "filename": "return-policy-old.md",
                    "status": "superseded",
                    "policy_authority": "official",
                    "audience": "customer",
                    "superseded_by": "RET-2026-01",
                },
                "content": (
                    "Customers may return items within "
                    "45 calendar days."
                ),
            },
        ]


def test_end_to_end_uses_current_policy_over_superseded_policy():
    retriever = FakeRetriever()

    agent = AIAgent(retriever)

    result = agent.run(
        "Can I return my shoes after 40 days?"
    )

    assert len(result.evidence.conflicts) == 1

    assert len(result.evidence.selected_documents) == 1

    selected = result.evidence.selected_documents[0]

    assert (
        selected["metadata"]["document_id"]
        == "RET-2026-01"
    )