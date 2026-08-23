from app.agent.agent import AIAgent


class FakeRetriever:
    def retrieve(self, query: str) -> list[dict]:
        return [
            {
                "metadata": {
                    "document_id": "RET-2026-01",
                    "status": "active",
                    "policy_authority": "official",
                    "audience": "customer",
                },
                "content": "Customers may return items within 30 calendar days.",
            },
            {
                "metadata": {
                    "document_id": "RET-2024-01",
                    "status": "superseded",
                    "policy_authority": "official",
                    "audience": "customer",
                    "superseded_by": "RET-2026-01",
                },
                "content": "Customers may return items within 45 calendar days.",
            },
        ]


def test_agent_retrieves_and_resolves_evidence():
    agent = AIAgent(FakeRetriever())

    result = agent.run(
        "Can I return my item after 40 days?"
    )

    assert result.question == "Can I return my item after 40 days?"

    assert len(result.evidence.conflicts) == 1

    assert len(result.evidence.selected_documents) == 1

    selected = result.evidence.selected_documents[0]

    assert (
        selected["metadata"]["document_id"]
        == "RET-2026-01"
    )