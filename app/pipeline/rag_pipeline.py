from dataclasses import dataclass
from typing import Optional

from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from app.rag.evidence_resolver import EvidenceResolver
from app.rag.answer_generator import AnswerGenerator
from app.rag.guard import EvidenceGuard
from app.rag.output_guard import OutputGuard
from app.rag.input_guard import InputGuard
from app.rag.policy_decision import PolicyDecisionLayer


@dataclass(frozen=True)
class PipelineResult:
    answer: str
    decision: str
    citations: list[str]
    input_guard_decision: Optional[str] = None
    evidence_guard_decision: Optional[str] = None
    output_guard_decision: Optional[str] = None


class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore("chroma_db")
        self.retriever = Retriever(self.vector_store, top_k=5)
        self.resolver = EvidenceResolver()
        self.input_guard = InputGuard()
        self.evidence_guard = EvidenceGuard()
        self.policy_decision_layer = PolicyDecisionLayer()
        self.generator = AnswerGenerator()
        self.output_guard = OutputGuard()

    def run(self, question: str, history: Optional[list] = None) -> PipelineResult:
        # 1. INPUT GUARD (We check the raw question first to block injections quickly)
        input_result = self.input_guard.check(question)
        if input_result.decision.value == "reject":
            if "empty" in input_result.reason.lower() or "whitespace" in input_result.reason.lower():
                return PipelineResult(
                    answer="Please enter a valid question.",
                    decision="reject",
                    citations=[],
                    input_guard_decision=input_result.decision.value,
                )
            else:
                return PipelineResult(
                    answer="I can't process that request because it contains an unsafe instruction.",
                    decision="reject",
                    citations=[],
                    input_guard_decision=input_result.decision.value,
                )

        # Resolve context if history is provided
        resolved_question = question
        if history:
            from app.rag.query_resolver import QueryContextResolver
            resolver = QueryContextResolver()
            resolved_question = resolver.resolve(question, history)

        # 2. RETRIEVE EVIDENCE using resolved question
        retrieved = self.retriever.retrieve(resolved_question)

        # 3. EVIDENCE RESOLUTION
        evidence = self.resolver.resolve(retrieved)

        # 4. EVIDENCE GUARD
        guard_result = self.evidence_guard.check(question, evidence)
        if guard_result.decision.value == "abstain":
            return PipelineResult(
                answer="I don't have enough reliable information in the available documents to answer this question.",
                decision="abstain",
                citations=[],
                input_guard_decision=input_result.decision.value,
                evidence_guard_decision=guard_result.decision.value,
            )

        if guard_result.decision.value == "human_handoff":
            return PipelineResult(
                answer="The available authoritative policies conflict. This requires human assistance.",
                decision="human_handoff",
                citations=[],
                input_guard_decision=input_result.decision.value,
                evidence_guard_decision=guard_result.decision.value,
            )

        # 5. POLICY DECISION LAYER
        policy_decision = self.policy_decision_layer.evaluate(question, evidence)

        # 6. GENERATE ANSWER USING NVIDIA
        result = self.generator.generate(question, evidence, policy_decision=policy_decision)

        # 7. OUTPUT GUARD
        output_result = self.output_guard.check(result.answer, evidence, question=question)
        
        # 8. FINAL RESPONSE CONSTRUCTION
        if output_result.decision.value == "allow":
            final_answer = result.answer
            decision = "answer"
            citations = result.citations
        elif output_result.decision.value == "reject":
            final_answer = "I could not verify the generated answer against the available policy evidence."
            decision = "reject"
            citations = []
        else:
            final_answer = "I do not have enough reliable evidence to answer this question."
            decision = "abstain"
            citations = []

        return PipelineResult(
            answer=final_answer,
            decision=decision,
            citations=citations,
            input_guard_decision=input_result.decision.value,
            evidence_guard_decision=guard_result.decision.value,
            output_guard_decision=output_result.decision.value,
        )
