from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorityResult:
    document_id: str
    authority_score: float
    status: str
    reason: str


class AuthorityResolver:
    """
    Determines document authority from explicit frontmatter metadata.

    This does not use filename tricks such as checking whether
    "current" or "legacy" appears in the filename.
    """

    def resolve(self, document: dict) -> AuthorityResult:
        metadata = document.get("metadata", {})

        document_id = metadata.get(
            "document_id",
            document.get("chunk_id", "unknown"),
        )

        status = str(metadata.get("status", "")).lower()
        policy_authority = str(
            metadata.get("policy_authority", "")
        ).lower()

        audience = str(
            metadata.get("audience", "")
        ).lower()

        customer_answering = metadata.get(
            "customer_answering",
            True,
        )

        score = 0.0
        reasons: list[str] = []

        # Explicit document lifecycle status.
        if status == "active":
            score += 100
            reasons.append("active")

        elif status == "superseded":
            score -= 100
            reasons.append("superseded")

        elif status == "draft":
            score -= 75
            reasons.append("draft")

        elif status:
            reasons.append(f"status={status}")

        # Explicit authority declaration.
        if policy_authority == "official":
            score += 50
            reasons.append("official authority")

        elif policy_authority in {"none", "internal", "unofficial"}:
            score -= 50
            reasons.append("not official authority")

        # Internal-only material must not be customer authority.
        if audience == "internal":
            score -= 50
            reasons.append("internal audience")

        # Explicitly marked as not suitable for customer answering.
        if customer_answering is False:
            score -= 100
            reasons.append("not for customer answering")

        if status == "active" and policy_authority == "official":
            authority_status = "authoritative"

        elif status == "superseded":
            authority_status = "superseded"

        elif status == "draft" or customer_answering is False:
            authority_status = "non_authoritative"

        else:
            authority_status = "normal"

        return AuthorityResult(
            document_id=document_id,
            authority_score=score,
            status=authority_status,
            reason="; ".join(reasons) or "no explicit authority signal",
        )

    def rank(
        self,
        documents: list[dict],
    ) -> list[tuple[dict, AuthorityResult]]:
        ranked = [
            (
                document,
                self.resolve(document),
            )
            for document in documents
        ]

        return sorted(
            ranked,
            key=lambda item: item[1].authority_score,
            reverse=True,
        )