import json
from dataclasses import dataclass
from typing import Optional

from app.llm.nvidia_client import NVIDIAClient
from app.rag.evidence_resolver import EvidenceResolution


@dataclass(frozen=True)
class PolicyDecision:
    is_applicable: bool
    is_within_window: Optional[bool]
    reasoning: str


class PolicyDecisionLayer:
    """
    Evaluates whether the customer's request falls within the policy limits.
    Produces a structured decision (WITHIN, OUTSIDE, UNKNOWN) which is then
    passed to the AnswerGenerator.
    """

    def __init__(self, llm_client: NVIDIAClient | None = None):
        self.llm_client = llm_client or NVIDIAClient()

    def evaluate(
        self,
        question: str,
        evidence: EvidenceResolution,
    ) -> PolicyDecision:

        if not evidence.selected_documents:
            return PolicyDecision(
                is_applicable=False,
                is_within_window=None,
                reasoning="No evidence provided."
            )

        context_parts = []
        for doc in evidence.selected_documents:
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("document_id", "unknown")
            content = doc.get("content", "").strip()
            context_parts.append(f"[Document: {doc_id}]\n{content}")
            
        context = "\n\n".join(context_parts)

        prompt = f"""
You are a strict extraction engine.
Analyze the customer's question and the authoritative evidence.
Extract the numeric values (in days) involved in the question.

Output ONLY valid JSON. No markdown formatting, no backticks, no conversational text.

Schema:
{{
    "is_applicable": bool, // true if the evidence covers the topic in the question
    "user_days": int or null, // The number of days the user is asking about (e.g. 40)
    "policy_days": int or null, // The maximum number of days allowed by the policy for this specific situation (e.g. 30)
    "reasoning": string // a brief explanation identifying the policy rule
}}

Question:
{question}

Evidence:
{context}
"""

        raw_response = self.llm_client.generate(prompt)

        try:
            start_idx = raw_response.find("{")
            end_idx = raw_response.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = raw_response[start_idx:end_idx]
                data = json.loads(json_str)
                
                is_within_window = None
                user_days = data.get("user_days")
                policy_days = data.get("policy_days")
                
                if isinstance(user_days, (int, float)) and isinstance(policy_days, (int, float)):
                    is_within_window = user_days <= policy_days
                    
                    if is_within_window:
                        reasoning = f"{user_days} days is less than or equal to the {policy_days}-day limit. Therefore, the request is within the policy window. ({data.get('reasoning', '')})"
                    else:
                        reasoning = f"{user_days} days is strictly greater than the {policy_days}-day limit. Therefore, the request is outside the policy window. ({data.get('reasoning', '')})"
                else:
                    reasoning = str(data.get("reasoning", ""))

                return PolicyDecision(
                    is_applicable=bool(data.get("is_applicable")),
                    is_within_window=is_within_window,
                    reasoning=reasoning
                )
        except Exception as e:
            pass

        return PolicyDecision(
            is_applicable=True,
            is_within_window=None,
            reasoning="Fallback decision: Could not parse LLM output."
        )
