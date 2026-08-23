from dataclasses import dataclass
import re

from app.rag.evidence_resolver import (
    EvidenceDecision,
    EvidenceResolution,
)
from app.llm.nvidia_client import NVIDIAClient


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    citations: list[str]
    decision: EvidenceDecision


class AnswerGenerator:
    """Generates grounded answers using NVIDIA LLM."""

    def __init__(self, llm_client: NVIDIAClient | None = None):
        self.llm_client = llm_client or NVIDIAClient()

    def generate(
        self,
        question: str,
        evidence: EvidenceResolution,
        policy_decision: "PolicyDecision" = None,
    ) -> GeneratedAnswer:

        # -----------------------------------------
        # ABSTAIN
        # -----------------------------------------
        if evidence.decision == EvidenceDecision.ABSTAIN:
            return GeneratedAnswer(
                answer=(
                    "I don't have enough reliable information "
                    "to answer this question."
                ),
                citations=[],
                decision=evidence.decision,
            )

        # -----------------------------------------
        # HUMAN HANDOFF
        # -----------------------------------------
        if evidence.decision == EvidenceDecision.HUMAN_HANDOFF:
            return GeneratedAnswer(
                answer=(
                    "The available authoritative information contains "
                    "a conflict. This requires human assistance."
                ),
                citations=self._build_citations(evidence),
                decision=evidence.decision,
            )

        # -----------------------------------------
        # GROUNDED ANSWER
        # -----------------------------------------
        context = self._build_context(
            evidence.selected_documents
        )

        decision_context = ""
        if policy_decision:
            decision_context = f"""
Policy Decision Engine Evaluation:
- Is request within policy window? {policy_decision.is_within_window if policy_decision.is_within_window is not None else "N/A"}
- Reasoning: {policy_decision.reasoning}
"""

        prompt = f"""
You are a customer-support assistant for an online retailer.

Use ONLY the authoritative evidence below to answer the customer's question.
Do not invent facts or use outside knowledge.

{decision_context}
Instructions:
1. Identify the policy rule that directly answers the customer's question.
2. Formulate your answer using the provided Policy Decision Engine Evaluation if available. State clearly whether the customer's request is within the policy window.
3. Keep your answer brief, direct, and concise.
4. Do NOT discuss unrelated policies, and do NOT discuss what the evidence does not cover.
5. Mention exceptions (e.g. TrailPlus) ONLY if they could materially change the outcome for this specific situation. Do NOT claim that exceptions do not exist simply because they are not mentioned.
6. If the evidence genuinely does not address the question, say you do not have enough reliable information.
7. On a new line at the very end of your answer, write "SOURCES: " followed
   by the exact [Document: ID] tags of the evidence you used.

Customer question:
{question}

Authoritative evidence:
{context}

Answer:
"""

        raw_answer = self.llm_client.generate(prompt)

        citations = self._build_citations(evidence, raw_answer)

        # Remove the SOURCES line from the final user-facing answer
        clean_answer = re.sub(r"\n*SOURCES:.*$", "", raw_answer, flags=re.IGNORECASE | re.MULTILINE).strip()

        return GeneratedAnswer(
            answer=clean_answer,
            citations=citations,
            decision=evidence.decision,
        )

    def _build_context(
        self,
        documents: list[dict],
    ) -> str:
        """
        Build a single context string from selected documents.

        Multiple chunks from the same document_id are merged into
        one block so the LLM sees each document once, reducing
        noise and preventing it from over-emphasising a document
        that happened to produce multiple retrieval hits.
        """

        if not documents:
            return ""

        # Merge chunks by document_id, preserving first-seen order.
        merged: dict[str, list[str]] = {}

        for document in documents:
            content = document.get("content", "").strip()

            if not content:
                continue

            metadata = document.get("metadata", {})

            document_id = metadata.get(
                "document_id",
                "unknown",
            )

            merged.setdefault(document_id, []).append(content)

        context_parts = []

        for document_id, chunks in merged.items():
            combined = "\n\n".join(chunks)

            context_parts.append(
                f"[Document: {document_id}]\n"
                f"{combined}"
            )

        return "\n\n".join(context_parts)

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
                "Knowledge base",
            )

            citations.append(
                f"{filename} — {heading}"
            )

        return citations