from dataclasses import dataclass
from enum import Enum
import re


class GuardDecision(str, Enum):
    ALLOW = "allow"
    ABSTAIN = "abstain"
    HUMAN_HANDOFF = "human_handoff"


@dataclass(frozen=True)
class GuardResult:
    decision: GuardDecision
    reason: str


class EvidenceGuard:
    """
    Validates retrieved evidence before the system generates an answer.

    The guard does NOT perform retrieval.
    It checks whether the retrieved evidence is safe and sufficient
    to continue.
    """

    def check(
        self,
        question: str,
        evidence_resolution,
    ) -> GuardResult:

        # ---------------------------------------------------------
        # 1. Empty question
        # ---------------------------------------------------------
        if not question or not question.strip():
            return GuardResult(
                decision=GuardDecision.ABSTAIN,
                reason="The question is empty.",
            )

        # ---------------------------------------------------------
        # 2. No authoritative evidence
        # ---------------------------------------------------------
        selected_documents = (
            evidence_resolution.selected_documents
        )

        if not selected_documents:
            return GuardResult(
                decision=GuardDecision.ABSTAIN,
                reason="No authoritative evidence was found.",
            )

        # ---------------------------------------------------------
        # 3. Authoritative conflict
        # ---------------------------------------------------------
        if evidence_resolution.decision.value == "human_handoff":
            return GuardResult(
                decision=GuardDecision.HUMAN_HANDOFF,
                reason="Authoritative sources contain a conflict.",
            )

        # ---------------------------------------------------------
        # 4. Check for obviously unsupported policy numbers
        #
        # Example:
        # Question: "Can I return after 40 days?"
        #
        # Evidence:
        # "return within 30 days"
        #
        # 40 does not need to appear in the document because
        # it is the customer's situation, not a policy value.
        # ---------------------------------------------------------
        question_days = self._extract_days(question)

        if question_days is not None:

            evidence_text = " ".join(
                document.get("content", "")
                for document in selected_documents
            ).lower()

            policy_days = self._extract_policy_return_days(
                evidence_text
            )

            if policy_days:
                # Evidence exists for a return-window question.
                return GuardResult(
                    decision=GuardDecision.ALLOW,
                    reason=(
                        "Authoritative evidence contains "
                        "a return-window policy."
                    ),
                )

        # ---------------------------------------------------------
        # 5. General evidence check & Relevance check
        # ---------------------------------------------------------
        usable_evidence = False
        
        # Extract meaningful words from the question
        question_words = set(re.findall(r"\b[a-z]{4,}\b", question.lower()))

        for document in selected_documents:
            content = document.get("content", "").strip().lower()

            if len(content) >= 20:
                if not question_words:
                    # If question doesn't have words >= 4 chars, just accept it
                    usable_evidence = True
                    break
                    
                doc_words = set(re.findall(r"\b[a-z]{4,}\b", content))
                # Check for substring matches (e.g. ship in ships/shipping) to allow stemming-like matching
                has_overlap = False
                for qw in question_words:
                    for dw in doc_words:
                        if qw in dw or dw in qw:
                            has_overlap = True
                            break
                    if has_overlap:
                        break
                
                # We require at least some semantic overlap to consider it relevant
                if has_overlap:
                    usable_evidence = True
                    break

        if not usable_evidence:
            return GuardResult(
                decision=GuardDecision.ABSTAIN,
                reason="Retrieved evidence is not relevant or insufficient to answer the question.",
            )

        # ---------------------------------------------------------
        # 6. Evidence is sufficient
        # ---------------------------------------------------------
        return GuardResult(
            decision=GuardDecision.ALLOW,
            reason="Authoritative evidence is available.",
        )

    @staticmethod
    def _extract_days(text: str):
        """
        Extract a number followed by 'day' or 'days'.

        Example:
            'return after 40 days'
            -> 40
        """

        match = re.search(
            r"\b(\d+)\s+days?\b",
            text.lower(),
        )

        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def _extract_policy_return_days(text: str):
        """
        Extract actual return-window policy values.

        We specifically look for return-related wording.

        Examples:
            'return within 30 calendar days'
            'return eligible within 45 days'
        """

        patterns = [
            r"return.{0,80}?within\s+(\d+)\s+calendar\s+days",
            r"return.{0,80}?within\s+(\d+)\s+days",
            r"within\s+(\d+)\s+calendar\s+days\s+of\s+delivery",
        ]

        values = []

        for pattern in patterns:
            matches = re.findall(pattern, text)

            for value in matches:
                values.append(int(value))

        return values