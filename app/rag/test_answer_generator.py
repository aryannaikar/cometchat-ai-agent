from app.agent.answer_generator import AnswerGenerator
from app.rag.evidence_resolver import EvidenceDecision, EvidenceResolution


def make_resolution(
    decision,
    selected_documents=None,
):
    return EvidenceResolution(
        decision=decision,
        selected_documents=selected_documents or [],
        evidence_items=[],
        conflicts=[],
        authority_results=[],
    )


def test_generates_grounded_answer_with_citation():
    generator = AnswerGenerator()

    documents = [
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": "Customers may return items within 30 calendar days.",
        }
    ]

    evidence = make_resolution(
        EvidenceDecision.ANSWER,
        documents,
    )

    result = generator.generate(
        "Can I return an item?",
        evidence,
    )

    assert result.decision == EvidenceDecision.ANSWER
    assert "30 calendar days" in result.answer
    assert "01-returns-policy-current.md" in result.citations[0]


def test_abstains_when_evidence_is_insufficient():
    generator = AnswerGenerator()

    evidence = make_resolution(
        EvidenceDecision.ABSTAIN
    )

    result = generator.generate(
        "Do you deliver to Mars?",
        evidence,
    )

    assert result.decision == EvidenceDecision.ABSTAIN
    assert " enough reliable information" in result.answer
    assert result.citations == []


def test_hands_off_when_authoritative_sources_conflict():
    generator = AnswerGenerator()

    documents = [
        {
            "metadata": {
                "filename": "policy-a.md",
                "document_id": "POLICY-A",
            },
            "content": "Returns are allowed within 30 days.",
        },
        {
            "metadata": {
                "filename": "policy-b.md",
                "document_id": "POLICY-B",
            },
            "content": "Returns are allowed within 45 days.",
        },
    ]

    evidence = make_resolution(
        EvidenceDecision.HUMAN_HANDOFF,
        documents,
    )

    result = generator.generate(
        "Can I return this after 40 days?",
        evidence,
    )

    assert result.decision == EvidenceDecision.HUMAN_HANDOFF
    assert "human assistance" in result.answer
    assert len(result.citations) == 2