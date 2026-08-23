from dataclasses import dataclass
from enum import Enum
import re


class OutputDecision(str, Enum):
    ALLOW = "allow"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class OutputGuardResult:
    decision: OutputDecision
    reason: str


class OutputGuard:
    """
    Checks whether the generated answer is supported
    by the authoritative evidence.

    Numeric values in the answer are verified against two
    sources:

    1. The user's original question  – values that the customer
       stated (e.g. "after 40 days", "$100") are allowed because
       they describe the customer's *situation*, not a policy claim.

    2. The authoritative evidence  – values that appear in the
       knowledge-base documents are allowed because they are
       verifiable policy facts.

    A numeric value that appears in *neither* source is treated as
    unsupported (possibly hallucinated by the LLM) and causes the
    answer to be rejected.
    """

    def check(
        self,
        answer: str,
        evidence,
        question: str = "",
    ) -> OutputGuardResult:

        if not answer or not answer.strip():
            return OutputGuardResult(
                OutputDecision.ABSTAIN,
                "The generated answer is empty.",
            )

        # Never allow an answer when authoritative evidence
        # itself contains an unresolved conflict.
        if evidence.decision.value == "human_handoff":
            return OutputGuardResult(
                OutputDecision.ABSTAIN,
                "Authoritative evidence contains a conflict.",
            )

        documents = evidence.selected_documents

        if not documents:
            return OutputGuardResult(
                OutputDecision.ABSTAIN,
                "No authoritative evidence is available.",
            )

        evidence_text = " ".join(
            document.get("content", "")
            for document in documents
        ).lower()

        answer_lower = answer.lower()
        question_lower = (question or "").lower()

        # ---------------------------------------------------------
        # Collect numbers from the user's question.
        # These are customer-provided values (situation, not policy)
        # and do not need evidence support.
        # ---------------------------------------------------------
        question_numbers = self._extract_all_numbers(
            question_lower,
        )

        # ---------------------------------------------------------
        # Check policy numbers mentioned in the answer.
        #
        # A day-count value in the answer is allowed if it comes
        # from the user's question OR from the authoritative
        # evidence.  Only values from *neither* source are
        # treated as unsupported.
        # ---------------------------------------------------------

        answer_days = self._extract_days(answer_lower)

        for days in answer_days:

            # User said this number → it's their situation, not
            # a policy claim the LLM invented.
            if days in question_numbers:
                continue

            # The number appears in the evidence text.
            if str(days) in evidence_text:
                continue

            return OutputGuardResult(
                OutputDecision.REJECT,
                f"The answer contains unsupported value: {days} days.",
            )

        # ---------------------------------------------------------
        # Check dollar amounts in the answer.
        # ---------------------------------------------------------

        answer_dollars = self._extract_dollars(answer_lower)

        for amount in answer_dollars:

            if amount in question_numbers:
                continue

            if str(amount) in evidence_text:
                continue

            return OutputGuardResult(
                OutputDecision.REJECT,
                f"The answer contains unsupported value: ${amount}.",
            )

        # ---------------------------------------------------------
        # Check important policy words.
        # ---------------------------------------------------------

        risky_claims = [
            "guaranteed",
            "definitely",
            "always",
            "never",
            "automatically approved",
        ]

        for claim in risky_claims:
            if claim in answer_lower and claim not in evidence_text:
                return OutputGuardResult(
                    OutputDecision.REJECT,
                    f"The answer contains an unsupported strong claim: '{claim}'.",
                )

        # ---------------------------------------------------------
        # Basic evidence overlap check.
        # ---------------------------------------------------------

        evidence_words = set(
            re.findall(r"\b[a-z]{4,}\b", evidence_text)
        )

        answer_words = set(
            re.findall(r"\b[a-z]{4,}\b", answer_lower)
        )

        overlap = evidence_words.intersection(answer_words)

        if len(overlap) < 3:
            return OutputGuardResult(
                OutputDecision.REJECT,
                "The answer has insufficient overlap with the evidence.",
            )

        return OutputGuardResult(
            OutputDecision.ALLOW,
            "The generated answer is supported by authoritative evidence.",
        )

    @staticmethod
    def _extract_days(text: str) -> list[int]:
        """Extract all N from 'N day(s)' patterns."""
        matches = re.findall(
            r"\b(\d+)\s+days?\b",
            text,
        )

        return [int(value) for value in matches]

    @staticmethod
    def _extract_dollars(text: str) -> list[int]:
        """Extract all N from '$N' or '$N.NN' patterns."""
        matches = re.findall(
            r"\$(\d+)(?:\.\d+)?",
            text,
        )

        return [int(value) for value in matches]

    @staticmethod
    def _extract_all_numbers(text: str) -> set[int]:
        """
        Extract every integer that appears in the text.

        This is used to build the set of user-provided numeric
        values that should be whitelisted.
        """
        matches = re.findall(r"\b(\d+)\b", text)

        return {int(value) for value in matches}