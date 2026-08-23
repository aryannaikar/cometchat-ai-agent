from app.agent.answer_generator import AnswerGenerator
from app.rag.evidence_resolver import (
    EvidenceDecision,
    EvidenceResolution,
)


class FakeLLM:
    """Fake NVIDIA client used for unit tests."""
    def generate(self, prompt: str) -> str:
        return "No. The return period is 30 calendar days.\nSOURCES: RET-2026-01"


class CustomFakeLLM:
    """Fake LLM that returns a pre-configured answer."""
    def __init__(self, answer: str):
        self._answer = answer

    def generate(self, prompt: str) -> str:
        return self._answer


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
    generator = AnswerGenerator(
        llm_client=FakeLLM()
    )

    documents = [
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "Customers may return items "
                "within 30 calendar days."
            ),
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

    assert (
        "01-returns-policy-current.md"
        in result.citations[0]
    )


def test_abstains_when_evidence_is_insufficient():
    generator = AnswerGenerator(
        llm_client=FakeLLM()
    )

    evidence = make_resolution(
        EvidenceDecision.ABSTAIN
    )

    result = generator.generate(
        "Do you deliver to Mars?",
        evidence,
    )

    assert result.decision == EvidenceDecision.ABSTAIN

    assert (
        "enough reliable information"
        in result.answer
    )

    assert result.citations == []


def test_hands_off_when_authoritative_sources_conflict():
    generator = AnswerGenerator(
        llm_client=FakeLLM()
    )

    documents = [
        {
            "metadata": {
                "filename": "policy-a.md",
                "document_id": "POLICY-A",
            },
            "content": (
                "Returns are allowed within 30 days."
            ),
        },
        {
            "metadata": {
                "filename": "policy-b.md",
                "document_id": "POLICY-B",
            },
            "content": (
                "Returns are allowed within 45 days."
            ),
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

    assert (
        result.decision
        == EvidenceDecision.HUMAN_HANDOFF
    )

    assert "human assistance" in result.answer

    assert len(result.citations) == 2


def test_citations_are_deduplicated():
    """
    When selected_documents contains multiple chunks from the same
    source file, _build_citations must produce only one citation
    per unique filename.
    """
    # Use a custom answer that overlaps with BOTH documents
    # to ensure both get cited exactly once.
    generator = AnswerGenerator(
        llm_client=CustomFakeLLM(
            "You can return items within 30 calendar days. "
            "Report damaged items within 7 calendar days.\n"
            "SOURCES: RET-2026-01, OPS-2026-04"
        )
    )

    documents = [
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "Customers may return items within "
                "30 calendar days."
            ),
        },
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "A $6.95 return shipping fee is deducted "
                "from the refund."
            ),
        },
        {
            "metadata": {
                "filename": "04-damaged-or-wrong-items.md",
                "document_id": "OPS-2026-04",
            },
            "content": (
                "Report damaged items within 7 calendar days."
            ),
        },
        {
            "metadata": {
                "filename": "04-damaged-or-wrong-items.md",
                "document_id": "OPS-2026-04",
            },
            "content": (
                "Final-sale items are eligible for review."
            ),
        },
    ]

    evidence = make_resolution(
        EvidenceDecision.ANSWER,
        documents,
    )

    result = generator.generate(
        "Can I return my shoes after 40 days?",
        evidence,
    )

    # Two unique filenames → exactly two citations.
    assert len(result.citations) == 2

    filenames = [c.split(" — ")[0] for c in result.citations]

    assert "01-returns-policy-current.md" in filenames
    assert "04-damaged-or-wrong-items.md" in filenames


def test_superseded_documents_are_not_cited():
    """
    When evidence.selected_documents contains only authoritative
    documents (superseded documents are excluded by
    EvidenceResolver), the citations must not include the
    superseded document.
    """
    generator = AnswerGenerator(
        llm_client=FakeLLM()
    )

    # Only the active document is in selected_documents;
    # the superseded document is NOT passed here
    # because EvidenceResolver already filtered it out.
    documents = [
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "Customers may return items within "
                "30 calendar days."
            ),
        },
    ]

    evidence = make_resolution(
        EvidenceDecision.ANSWER,
        documents,
    )

    result = generator.generate(
        "Can I return my shoes after 40 days?",
        evidence,
    )

    assert len(result.citations) == 1
    assert "01-returns-policy-current.md" in result.citations[0]

    # Superseded doc must not appear anywhere in citations.
    for citation in result.citations:
        assert "02-returns-policy-legacy" not in citation
        assert "RET-2024-01" not in citation


def test_citation_order_is_preserved():
    """
    Citations must appear in the same order as the documents
    were first encountered in selected_documents.
    """
    # Answer overlaps with both
    generator = AnswerGenerator(
        llm_client=CustomFakeLLM(
            "You can return items within 30 calendar days. "
            "Report damaged items within 7 calendar days.\n"
            "SOURCES: RET-2026-01, OPS-2026-04"
        )
    )

    documents = [
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "Customers may return items within "
                "30 calendar days."
            ),
        },
        {
            "metadata": {
                "filename": "04-damaged-or-wrong-items.md",
                "document_id": "OPS-2026-04",
            },
            "content": (
                "Report damaged items within 7 calendar days."
            ),
        },
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "A $6.95 return shipping fee applies."
            ),
        },
    ]

    evidence = make_resolution(
        EvidenceDecision.ANSWER,
        documents,
    )

    result = generator.generate(
        "Can I return my shoes?",
        evidence,
    )

    assert len(result.citations) == 2

    # First-seen order: returns-policy first, then damaged-items.
    assert "01-returns-policy-current.md" in result.citations[0]
    assert "04-damaged-or-wrong-items.md" in result.citations[1]


def test_retrieved_but_unused_document_is_not_cited():
    """
    If a document is retrieved but its content does not support
    (i.e., has no meaningful overlap with) the generated answer,
    it must not be cited.
    """
    generator = AnswerGenerator(
        llm_client=CustomFakeLLM(
            "You can return items within 30 calendar days.\n"
            "SOURCES: RET-2026-01"
        )
    )

    documents = [
        {
            "metadata": {
                "filename": "01-returns-policy-current.md",
                "document_id": "RET-2026-01",
            },
            "content": (
                "Customers may return items within "
                "30 calendar days."
            ),
        },
        {
            "metadata": {
                "filename": "04-damaged-or-wrong-items.md",
                "document_id": "OPS-2026-04",
            },
            "content": (
                "Customers must report damaged products in one week."
            ),
        },
    ]

    evidence = make_resolution(
        EvidenceDecision.ANSWER,
        documents,
    )

    result = generator.generate(
        "Can I return my shoes?",
        evidence,
    )

    # Only 1 citation because the damaged-items doc doesn't overlap
    # with the generated answer.
    assert len(result.citations) == 1
    assert "01-returns-policy-current.md" in result.citations[0]
    assert "04-damaged-or-wrong-items.md" not in result.citations[0]