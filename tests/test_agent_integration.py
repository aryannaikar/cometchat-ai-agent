from app.agent.agent import AIAgent
from app.rag.evidence_resolver import EvidenceDecision


class FakeRetriever:
    def retrieve(self, query: str):
        return [
            {
                "metadata": {
                    "document_id": "RET-2026-01",
                    "filename": "01-returns-policy-current.md",
                    "status": "active",
                    "policy_authority": "official",
                    "audience": "customer",
                },
                "content": (
                    "Customers may return items "
                    "within 30 calendar days."
                ),
            }
        ]


class FakeNVIDIAClient:
    def generate(self, prompt: str) -> str:
        return "Yes, you can return an item within 30 calendar days.\nSOURCES: RET-2026-01"


def test_agent_returns_answer_with_evidence_and_citation():
    agent = AIAgent(FakeRetriever())
    agent.answer_generator.llm_client = FakeNVIDIAClient()

    result = agent.run(
        "Can I return an item?"
    )

    assert result.question == "Can I return an item?"

    assert result.evidence.selected_documents

    assert result.answer.decision == EvidenceDecision.ANSWER

    assert "30 calendar days" in result.answer.answer

    assert (
        "01-returns-policy-current.md"
        in result.answer.citations[0]
    )