from dataclasses import dataclass
import re

from app.llm.nvidia_client import NVIDIAClient
from app.llm.prompt_builder import GroundedPromptBuilder
from app.rag.evidence_resolver import (
    EvidenceDecision,
    EvidenceResolution,
)


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    citations: list[str]
    decision: EvidenceDecision


class AnswerGenerator:
    """Generates a grounded answer from resolved evidence."""

    def __init__(
        self,
        llm_client=None,
        prompt_builder=None,
    ):
        self.llm_client = llm_client or NVIDIAClient()
        self.prompt_builder = prompt_builder or GroundedPromptBuilder()

    def generate(
        self,
        question: str,
        evidence: EvidenceResolution,
    ) -> GeneratedAnswer:

        # Do not call the LLM when we must abstain.
        if evidence.decision == EvidenceDecision.ABSTAIN:
            return GeneratedAnswer(
                answer=(
                    "I don't have enough reliable information "
                    "to answer this question."
                ),
                citations=[],
                decision=evidence.decision,
            )

        # Do not let the LLM resolve authoritative conflicts.
        if evidence.decision == EvidenceDecision.HUMAN_HANDOFF:
            return GeneratedAnswer(
                answer=(
                    "The available authoritative information contains "
                    "a conflict. This requires human assistance."
                ),
                citations=self._build_citations(evidence),
                decision=evidence.decision,
            )

        # Only approved evidence reaches the LLM.
        prompt = self.prompt_builder.build(
            question=question,
            evidence=evidence.selected_documents,
        )

        raw_answer = self.llm_client.generate(prompt)

        clean_answer = re.sub(r"\n*SOURCES:.*$", "", raw_answer, flags=re.IGNORECASE | re.MULTILINE).strip()

        return GeneratedAnswer(
            answer=clean_answer,
            citations=self._build_citations(evidence, raw_answer),
            decision=evidence.decision,
        )

    def _build_citations(
        self,
        evidence: EvidenceResolution,
        answer: str = "",
    ) -> list[str]:
        """
        Build a deduplicated citation list from selected documents.

        Multiple chunks from the same source file produce only one
        citation entry.  First-seen order is preserved.
        
        Only cites documents that have meaningful word overlap
        with the generated answer, avoiding citations for
        retrieved but unused documents.
        """

        seen_filenames: set[str] = set()
        citations: list[str] = []

        # Only cite documents that were explicitly referenced by the LLM
        for document in evidence.selected_documents:
            metadata = document.get("metadata", {})
            document_id = metadata.get("document_id", "")
            filename = metadata.get("filename", metadata.get("source", "unknown"))

            if filename in seen_filenames:
                continue
                
            # If we have an answer, verify the LLM cited this document ID
            if answer and document_id:
                if document_id not in answer:
                    continue

            seen_filenames.add(filename)

            heading = metadata.get(
                "heading",
                "Unknown section",
            )

            citations.append(
                f"{filename} — {heading}"
            )

        return citations