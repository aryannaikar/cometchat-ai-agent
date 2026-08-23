from dataclasses import dataclass
from enum import Enum

from app.rag.authority import AuthorityResolver, AuthorityResult
from app.rag.conflict_detector import Conflict, ConflictDetector


class EvidenceDecision(str, Enum):
    ANSWER = "answer"
    ABSTAIN = "abstain"
    HUMAN_HANDOFF = "human_handoff"


@dataclass(frozen=True)
class EvidenceItem:
    document: dict
    authority: AuthorityResult
    category: str


@dataclass(frozen=True)
class EvidenceResolution:
    selected_documents: list[dict]
    evidence_items: list[EvidenceItem]
    conflicts: list[Conflict]
    authority_results: list[AuthorityResult]
    decision: EvidenceDecision


class EvidenceResolver:
    """
    Combines conflict detection and authority resolution.

    Historical/superseded documents do not create a human handoff
    when a current authoritative document is available.
    """

    def __init__(self):
        self.conflict_detector = ConflictDetector()
        self.authority_resolver = AuthorityResolver()

    def resolve(
        self,
        documents: list[dict],
    ) -> EvidenceResolution:

        conflicts = self.conflict_detector.detect(documents)

        ranked = self.authority_resolver.rank(documents)

        evidence_items = []

        for document, authority in ranked:

            if authority.status == "authoritative":
                category = "authoritative"

            elif authority.status == "superseded":
                category = "historical"

            elif authority.status == "non_authoritative":
                category = "non_authoritative"

            else:
                category = "normal"

            evidence_items.append(
                EvidenceItem(
                    document=document,
                    authority=authority,
                    category=category,
                )
            )

        authority_results = [
            item.authority
            for item in evidence_items
        ]

        # Only current authoritative documents are selected
        # for the final answer.
        selected_documents = [
            item.document
            for item in evidence_items
            if item.category == "authoritative"
        ]

        if not selected_documents:
            decision = EvidenceDecision.ABSTAIN

        elif self._has_authoritative_conflict(
            evidence_items,
            conflicts,
        ):
            decision = EvidenceDecision.HUMAN_HANDOFF

        else:
            decision = EvidenceDecision.ANSWER

        return EvidenceResolution(
            selected_documents=selected_documents,
            evidence_items=evidence_items,
            conflicts=conflicts,
            authority_results=authority_results,
            decision=decision,
        )

    def _has_authoritative_conflict(
        self,
        evidence_items: list[EvidenceItem],
        conflicts: list[Conflict],
    ) -> bool:
        """
        A conflict requires at least TWO authoritative documents.

        Example:

        Current 30-day policy
        +
        Superseded 45-day policy

        => NOT a real current conflict.

        But:

        Current Policy A: 30 days
        +
        Current Policy B: 45 days

        => REAL conflict -> human handoff.
        """

        authoritative_ids = {
            item.authority.document_id
            for item in evidence_items
            if item.category == "authoritative"
        }

        for conflict in conflicts:
            conflicting_ids = set(conflict.documents)

            authoritative_conflicting_ids = (
                authoritative_ids.intersection(
                    conflicting_ids
                )
            )

            # Historical/non-authoritative documents
            # cannot cause a current-policy handoff.
            if len(authoritative_conflicting_ids) >= 2:
                return True

        return False