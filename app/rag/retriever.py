class Retriever:
    """Retrieves and reranks knowledge-base evidence."""

    def __init__(self, vector_store, top_k: int = 5):
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, question: str) -> list[dict]:
        # Retrieve more candidates from Chroma first.
        candidates = self.vector_store.search(
            question,
            top_k=max(self.top_k, 10),
        )

        # Rerank using authority + content relevance.
        candidates.sort(
            key=lambda document: self._rerank_score(
                document,
                question,
            ),
            reverse=True,
        )

        # Document-level deduplication: merge chunks from the same document
        merged_candidates = []
        seen_docs = {}

        for doc in candidates:
            doc_id = doc.get("metadata", {}).get("document_id")
            if not doc_id:
                merged_candidates.append(doc)
                continue
                
            if doc_id not in seen_docs:
                doc_copy = doc.copy()
                seen_docs[doc_id] = doc_copy
                merged_candidates.append(doc_copy)
            else:
                existing_doc = seen_docs[doc_id]
                # Avoid appending exact duplicate text
                if doc.get("content", "").strip() not in existing_doc.get("content", ""):
                    existing_doc["content"] = existing_doc["content"] + "\n\n[...]\n\n" + doc.get("content", "")

        return merged_candidates[:self.top_k]

    @staticmethod
    def _rerank_score(
        document: dict,
        question: str,
    ) -> float:

        metadata = document.get("metadata", {})
        content = document.get("content", "").lower()
        question = question.lower()

        # Chroma distance:
        # smaller distance = more semantically similar.
        distance = document.get("distance", 999)

        # Start with semantic relevance.
        score = -distance

        status = metadata.get("status")
        authority = metadata.get("policy_authority")
        audience = metadata.get("audience")

        # =========================================
        # AUTHORITY SCORING
        # =========================================

        # Prefer active documents.
        if status == "active":
            score += 2.0

        # Prefer official policies.
        if authority == "official":
            score += 2.0

        # Prefer customer-facing information.
        if audience == "customer":
            score += 1.0

        # =========================================
        # PENALTIES
        # =========================================

        # Historical policies should not dominate.
        if status == "superseded":
            score -= 3.0

        # Draft policies should not be used as authoritative answers.
        if status == "draft":
            score -= 3.0

        # Internal-only documents are less useful for customer answers.
        if audience == "internal":
            score -= 1.0

        # =========================================
        # GENERAL CONTENT RELEVANCE
        # =========================================

        important_terms = [
            "return",
            "returns",
            "days",
            "delivery",
            "refund",
            "eligible",
        ]

        for term in important_terms:
            if term in question and term in content:
                score += 0.5

        # =========================================
        # RETURN-WINDOW RELEVANCE
        # =========================================

        # Stronger boost for chunks that actually
        # describe the return-period rule.
        return_window_phrases = [
            "return window",
            "return within",
            "calendar days of delivery",
            "days of delivery",
        ]

        for phrase in return_window_phrases:
            if phrase in content:
                score += 2.0

        return score