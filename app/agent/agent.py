from dataclasses import dataclass

from app.agent.answer_generator import (
    AnswerGenerator,
    GeneratedAnswer,
)
from app.rag.evidence_resolver import EvidenceResolution, EvidenceResolver


@dataclass(frozen=True)
class AgentResult:
    question: str
    evidence: EvidenceResolution
    answer: GeneratedAnswer


class AIAgent:
    """Coordinates retrieval, evidence resolution, and answer generation."""

    def __init__(self, retriever):
        self.retriever = retriever
        self.evidence_resolver = EvidenceResolver()
        self.answer_generator = AnswerGenerator()

    def run(self, question: str) -> AgentResult:
        documents = self.retriever.retrieve(question)

        evidence = self.evidence_resolver.resolve(documents)

        answer = self.answer_generator.generate(
            question=question,
            evidence=evidence,
        )

        return AgentResult(
            question=question,
            evidence=evidence,
            answer=answer,
        )