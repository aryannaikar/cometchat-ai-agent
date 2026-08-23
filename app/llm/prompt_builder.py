class GroundedPromptBuilder:
    """Builds prompts that restrict the LLM to approved evidence."""

    def build(
        self,
        question: str,
        evidence: list[dict],
    ) -> str:

        evidence_text = "\n\n".join(
            f"[Document: {document.get('metadata', {}).get('document_id', 'unknown')}]\n{document.get('content', '').strip()}"
            for document in evidence
            if document.get("content", "").strip()
        )

        return f"""
You are a customer support assistant.

Answer the user's question using ONLY the evidence provided below.

Rules:
- Identify the policy rule that directly answers the user's question and apply it to their situation. For example, if a user asks about a return after X days, and the policy allows Y days, state clearly whether X is within Y.
- Keep your answer brief, direct, and concise.
- Do NOT invent information or use knowledge outside the provided evidence.
- Do NOT discuss unrelated policies, and do NOT discuss what the evidence does not cover.
- Mention exceptions ONLY if they could materially change the outcome for this specific situation. Do NOT claim that exceptions do not exist simply because they are not mentioned.
- If the evidence does not answer the question, say that you do not have enough reliable information.
- On a new line at the very end of your answer, write "SOURCES: " followed by the exact [Document: ID] tags of the evidence you used.

User question:
{question}

Approved evidence:
{evidence_text}

Answer:
""".strip()