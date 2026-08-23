from app.rag.evidence_resolver import EvidenceResolver
from app.rag.evidence_resolver import EvidenceDecision

def test_selects_active_official_policy_over_superseded_policy():
    resolver = EvidenceResolver()

    documents = [
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

    result = resolver.resolve(documents)

    assert len(result.conflicts) == 1

    assert len(result.selected_documents) == 1

    assert (
        result.selected_documents[0]["metadata"]["document_id"]
        == "RET-2026-01"
    )


def test_draft_internal_policy_is_not_selected():
    resolver = EvidenceResolver()

    documents = [
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
                "document_id": "MIG-2026-04",
                "status": "draft",
                "policy_authority": None,
                "audience": "internal",
                "customer_answering": False,
            },
            "content": "Migration draft suggests a 60 day return period.",
        },
    ]

    result = resolver.resolve(documents)

    assert len(result.selected_documents) == 1

    assert (
        result.selected_documents[0]["metadata"]["document_id"]
        == "RET-2026-01"
    )

def test_superseded_policy_is_classified_as_historical():
    resolver = EvidenceResolver()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2024-01",
                "status": "superseded",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": "Customers may return items within 45 calendar days.",
        }
    ]

    result = resolver.resolve(documents)

    assert len(result.evidence_items) == 1

    item = result.evidence_items[0]

    assert item.category == "historical"
    assert item.authority.status == "superseded"


def test_internal_draft_is_classified_as_non_authoritative():
    resolver = EvidenceResolver()

    documents = [
        {
            "metadata": {
                "document_id": "MIG-2026-04",
                "status": "draft",
                "policy_authority": None,
                "audience": "internal",
                "customer_answering": False,
            },
            "content": "Migration draft suggests a 60 day return period.",
        }
    ]

    result = resolver.resolve(documents)

    assert len(result.evidence_items) == 1

    item = result.evidence_items[0]

    assert item.category == "non_authoritative"
    assert item.authority.status == "non_authoritative"

def test_current_authoritative_conflict_requires_human_handoff():
    resolver = EvidenceResolver()

    documents = [
        {
            "metadata": {
                "document_id": "POLICY-A",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": "Customers may return items within 30 days.",
        },
        {
            "metadata": {
                "document_id": "POLICY-B",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": "Customers may return items within 45 days.",
        },
    ]

    result = resolver.resolve(documents)

    assert len(result.conflicts) == 1
    assert result.decision == EvidenceDecision.HUMAN_HANDOFF


def test_no_authoritative_evidence_causes_abstention():
    resolver = EvidenceResolver()

    documents = [
        {
            "metadata": {
                "document_id": "MIG-2026-04",
                "status": "draft",
                "policy_authority": None,
                "audience": "internal",
                "customer_answering": False,
            },
            "content": "Migration draft suggests a 60 day return period.",
        }
    ]

    result = resolver.resolve(documents)

    assert result.selected_documents == []
    assert result.decision == EvidenceDecision.ABSTAIN


def test_cross_topic_policy_does_not_trigger_human_handoff():
    """
    OPS-2026-04 governs damage/wrong-item *reporting* (7 days).
    RET-2026-01 governs standard *returns* (30 days).
    These are different policy questions and must NOT conflict.
    The resolution should be ANSWER using RET-2026-01.
    """
    resolver = EvidenceResolver()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2026-01",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": (
                "Customers on the standard plan may request a return "
                "within 30 calendar days of delivery."
            ),
        },
        {
            "metadata": {
                "document_id": "OPS-2026-04",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": (
                "Customers should report an item that arrived damaged, "
                "visibly defective, or different from what was ordered "
                "within 7 calendar days of delivery."
            ),
        },
    ]

    result = resolver.resolve(documents)

    # No return-window conflict detected.
    assert result.conflicts == []
    # Both docs are authoritative; RET-2026-01 is selected.
    assert result.decision == EvidenceDecision.ANSWER


def test_real_world_retrieval_scenario_resolves_to_answer():
    """
    Full real-world scenario: 5 retrieved chunks including
    RET-2026-01 (active), OPS-2026-04 (active, damage reporting),
    and RET-2024-01 (superseded).

    The expected outcome is ANSWER — only RET-2026-01 is authoritative
    for the return-window question; OPS-2026-04's 7-day reporting window
    is a different topic; RET-2024-01 is superseded and cannot cause a
    human handoff by itself.
    """
    resolver = EvidenceResolver()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2026-01",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": (
                "Customers on the standard plan may request a return "
                "within 30 calendar days of delivery."
            ),
        },
        {
            "metadata": {
                "document_id": "OPS-2026-04",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": (
                "Customers should report an item that arrived damaged "
                "within 7 calendar days of delivery."
            ),
        },
        {
            "metadata": {
                "document_id": "RET-2024-01",
                "status": "superseded",
                "policy_authority": "official",
                "audience": "customer",
                "superseded_by": "RET-2026-01",
            },
            "content": (
                "This document applied to orders placed before "
                "April 1, 2026. It has been superseded by RET-2026-01. "
                "Customers could return eligible merchandise within "
                "45 calendar days of delivery."
            ),
        },
        {
            "metadata": {
                "document_id": "OPS-2026-04",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": (
                "A manufacturing defect reported after the seven-day "
                "arrival window may be considered under the Warranty Policy."
            ),
        },
        {
            "metadata": {
                "document_id": "RET-2026-01",
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
            "content": (
                "A $6.95 return shipping fee is deducted from the refund "
                "for standard domestic returns."
            ),
        },
    ]

    result = resolver.resolve(documents)

    # Decision must be ANSWER, not HUMAN_HANDOFF.
    assert result.decision == EvidenceDecision.ANSWER

    # Only authoritative documents are selected.
    selected_ids = {
        doc["metadata"]["document_id"]
        for doc in result.selected_documents
    }
    assert "RET-2026-01" in selected_ids
    assert "RET-2024-01" not in selected_ids