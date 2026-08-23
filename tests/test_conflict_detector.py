from app.rag.conflict_detector import ConflictDetector


def test_no_conflict_returns_empty_list():
    detector = ConflictDetector()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2026-01",
            },
            "content": "Returns are accepted within 30 days.",
        }
    ]

    conflicts = detector.detect(documents)

    assert conflicts == []


def test_detects_conflicting_return_windows():
    detector = ConflictDetector()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2026-01",
            },
            "content": "Customers may return items within 30 calendar days.",
        },
        {
            "metadata": {
                "document_id": "RET-2024-01",
            },
            "content": "Customers may return items within 45 calendar days.",
        },
    ]

    conflicts = detector.detect(documents)

    assert len(conflicts) == 1

    conflict = conflicts[0]

    assert conflict.topic == "return_window"
    assert "RET-2026-01" in conflict.documents
    assert "RET-2024-01" in conflict.documents
    assert "30 days" in conflict.description
    assert "45 days" in conflict.description


def test_reporting_window_does_not_conflict_with_return_window():
    """
    A damage-reporting deadline ("report within 7 days") in OPS-2026-04
    must NOT be treated as a return-window conflict with RET-2026-01's
    30-day return window.  The two numbers address entirely different
    policy questions.
    """
    detector = ConflictDetector()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2026-01",
                "status": "active",
                "policy_authority": "official",
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
            },
            "content": (
                "Customers should report an item that arrived damaged, "
                "visibly defective, or different from what was ordered "
                "within 7 calendar days of delivery."
            ),
        },
    ]

    conflicts = detector.detect(documents)

    # The two windows govern different topics; no return-window conflict.
    assert conflicts == []


def test_superseded_return_window_still_detected_as_numeric_conflict():
    """
    When a superseded document contains a different return-window value,
    the ConflictDetector reports the numeric disagreement.
    Whether it causes a human handoff is EvidenceResolver's concern
    (it requires >= 2 *authoritative* documents in the conflict set).
    """
    detector = ConflictDetector()

    documents = [
        {
            "metadata": {
                "document_id": "RET-2026-01",
                "status": "active",
                "policy_authority": "official",
            },
            "content": (
                "Customers may request a return within 30 calendar days "
                "of delivery."
            ),
        },
        {
            "metadata": {
                "document_id": "RET-2024-01",
                "status": "superseded",
                "policy_authority": "official",
                "superseded_by": "RET-2026-01",
            },
            "content": (
                "Customers could return eligible merchandise within "
                "45 calendar days of delivery."
            ),
        },
    ]

    conflicts = detector.detect(documents)

    # Numeric disagreement IS detected …
    assert len(conflicts) == 1
    assert "RET-2026-01" in conflicts[0].documents
    assert "RET-2024-01" in conflicts[0].documents
    # … but EvidenceResolver will NOT escalate because RET-2024-01
    # is superseded (non-authoritative).