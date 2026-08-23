from app.rag.output_guard import OutputGuard, OutputDecision
from app.rag.evidence_resolver import EvidenceDecision, EvidenceResolution


def _make_evidence(documents, decision=EvidenceDecision.ANSWER):
    """Build a minimal EvidenceResolution for testing."""
    return EvidenceResolution(
        selected_documents=documents,
        evidence_items=[],
        conflicts=[],
        authority_results=[],
        decision=decision,
    )


# -----------------------------------------------------------------
# 1. User says "40 days", evidence says "30 days" → ALLOW
# -----------------------------------------------------------------

def test_user_provided_value_is_whitelisted():
    """
    '40 days' comes from the user's question, not a policy claim.
    '30 calendar days' comes from evidence.
    The guard must ALLOW.
    """
    guard = OutputGuard()

    evidence = _make_evidence([
        {
            "metadata": {"document_id": "RET-2026-01"},
            "content": (
                "Customers on the standard plan may request a "
                "return within 30 calendar days of delivery."
            ),
        },
    ])

    result = guard.check(
        answer=(
            "The customer is asking to return their shoes "
            "after 40 days, which is outside the standard "
            "return window of 30 calendar days of delivery."
        ),
        evidence=evidence,
        question="Can I return my shoes after 40 days?",
    )

    assert result.decision == OutputDecision.ALLOW


# -----------------------------------------------------------------
# 2. Answer invents "60 days" — neither question nor evidence → REJECT
# -----------------------------------------------------------------

def test_hallucinated_value_is_rejected():
    """
    '60 days' appears in neither the user's question nor the evidence.
    The guard must REJECT this as an unsupported hallucination.
    """
    guard = OutputGuard()

    evidence = _make_evidence([
        {
            "metadata": {"document_id": "RET-2026-01"},
            "content": (
                "Customers may request a return within "
                "30 calendar days of delivery."
            ),
        },
    ])

    result = guard.check(
        answer=(
            "You can return items within 60 days of delivery."
        ),
        evidence=evidence,
        question="Can I return my shoes after 40 days?",
    )

    assert result.decision == OutputDecision.REJECT
    assert "60 days" in result.reason


# -----------------------------------------------------------------
# 3. Answer correctly repeats evidence-supported "30 days" → ALLOW
# -----------------------------------------------------------------

def test_evidence_supported_value_is_allowed():
    """
    '30 days' is directly supported by the evidence.
    The guard must ALLOW.
    """
    guard = OutputGuard()

    evidence = _make_evidence([
        {
            "metadata": {"document_id": "RET-2026-01"},
            "content": (
                "Customers may request a return within "
                "30 calendar days of delivery."
            ),
        },
    ])

    result = guard.check(
        answer=(
            "The standard return window is 30 days from delivery."
        ),
        evidence=evidence,
        question="What is the return window?",
    )

    assert result.decision == OutputDecision.ALLOW


# -----------------------------------------------------------------
# 4. User says "$100", answer invents "$200" → REJECT
# -----------------------------------------------------------------

def test_hallucinated_dollar_amount_is_rejected():
    """
    The user mentioned '$100', which is allowed.
    '$200' appears in neither the question nor the evidence.
    The guard must REJECT.
    """
    guard = OutputGuard()

    evidence = _make_evidence([
        {
            "metadata": {"document_id": "RET-2026-01"},
            "content": (
                "A $6.95 return shipping fee is deducted from "
                "the refund for standard domestic returns."
            ),
        },
    ])

    result = guard.check(
        answer=(
            "Your $100 item qualifies for a return, and you "
            "will receive a $200 refund."
        ),
        evidence=evidence,
        question="I paid $100 for this item, can I return it?",
    )

    assert result.decision == OutputDecision.REJECT
    assert "$200" in result.reason


# -----------------------------------------------------------------
# 5. User-provided numbers do NOT become evidence claims
# -----------------------------------------------------------------

def test_user_numbers_do_not_become_evidence_claims():
    """
    The user said '40 days'.  The answer also says '40 days'.
    This must be ALLOWED because '40' comes from the user's question.
    It must NOT require '40' to exist in the evidence.

    But if the answer also invents a number that is in NEITHER
    the question NOR the evidence, it must still be rejected.
    """
    guard = OutputGuard()

    evidence = _make_evidence([
        {
            "metadata": {"document_id": "RET-2026-01"},
            "content": (
                "Customers may request a return within "
                "30 calendar days of delivery."
            ),
        },
    ])

    # Allowed: answer repeats user's "40" and evidence's "30"
    result_ok = guard.check(
        answer=(
            "Customers on the standard plan may request a "
            "return within 30 calendar days of delivery. "
            "Since 40 days have passed, the request is "
            "outside the standard return window."
        ),
        evidence=evidence,
        question="Can I return my shoes after 40 days?",
    )

    assert result_ok.decision == OutputDecision.ALLOW

    # Rejected: answer invents "90 days" beyond user + evidence
    result_bad = guard.check(
        answer=(
            "Customers may request a return within "
            "90 days of delivery, so your 40 day request "
            "is within the return window."
        ),
        evidence=evidence,
        question="Can I return my shoes after 40 days?",
    )

    assert result_bad.decision == OutputDecision.REJECT
    assert "90 days" in result_bad.reason


# -----------------------------------------------------------------
# Backward compatibility: check() without question still works
# -----------------------------------------------------------------

def test_check_without_question_still_works():
    """
    Calling check(answer, evidence) without question= must not crash.
    It should still ALLOW when all answer values exist in the evidence.
    """
    guard = OutputGuard()

    evidence = _make_evidence([
        {
            "metadata": {"document_id": "RET-2026-01"},
            "content": (
                "Customers may request a return within "
                "30 calendar days of delivery."
            ),
        },
    ])

    result = guard.check(
        answer=(
            "Customers may request a return within "
            "30 calendar days of delivery."
        ),
        evidence=evidence,
    )

    assert result.decision == OutputDecision.ALLOW
