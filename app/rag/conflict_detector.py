from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Conflict:
    topic: str
    documents: list[str]
    description: str


class ConflictDetector:
    """
    Detects conflicting return-window values across retrieved evidence.

    The detector is topic-aware: it only extracts day values that appear in
    a *return window* semantic context (e.g. "return within 30 days",
    "request a return within 30 calendar days").

    Day values in unrelated contexts — such as a damage-reporting deadline
    ("report within 7 days"), a refund-processing timeframe ("processed
    within 5–7 business days"), or a shipping estimate — are deliberately
    ignored.  This prevents policies that govern different questions
    (e.g. OPS-2026-04's 7-day damage-reporting window vs. RET-2026-01's
    30-day return window) from being treated as a genuine return-policy
    conflict.

    A genuine conflict exists when two *different* documents both contain
    an explicit return-window value and those values disagree.  Whether that
    conflict rises to the level of requiring a human handoff is decided
    upstream by EvidenceResolver (which additionally requires both documents
    to be currently authoritative).
    """

    # Matches "<verb phrase> within <N> [calendar] day(s)".
    # The verb phrase must contain a return-related word
    # (return / send back / request a return / eligible for return, etc.)
    # within a short look-behind window so that damage-reporting,
    # refund-processing, and shipping contexts are excluded.
    #
    # The look-behind is not a fixed-width look-behind because the verb
    # phrase can vary in length, so we use a combined approach:
    # capture the surrounding sentence fragment and then validate it.
    _CONTEXT_PATTERN = re.compile(
        r"(?P<ctx>[^.!?\n]{0,120}?)"          # up to 120 chars of context
        r"\b(?P<days>\d+)"                     # the number
        r"\s+(?:calendar\s+)?days?\b",         # "days" / "calendar days"
        re.IGNORECASE,
    )

    # Words that indicate the surrounding context IS a return-window statement.
    _RETURN_VERBS = re.compile(
        r"\b(?:return|returns|send\s+back|request(?:ing)?\s+a\s+return"
        r"|eligible\s+for\s+a?\s*return|return\s+eligible)\b",
        re.IGNORECASE,
    )

    # Words that indicate the surrounding context is NOT a return window
    # (damage reporting, refund timing, shipping, inspection, etc.).
    _EXCLUDED_VERBS = re.compile(
        r"\b(?:report|reporting|process(?:ed|ing)?|inspect(?:ed|ing)?"
        r"|ship(?:ping|ped)?|deliver(?:ed|y)?|business\s+day"
        r"|arrival\s+window|after\s+(?:the\s+)?(?:seven|7)[\s-]day"
        r")\b",
        re.IGNORECASE,
    )

    def _extract_return_window_days(self, content: str) -> list[int]:
        """
        Return all day-count integers that appear in a return-window
        context within *content*.  Values in non-return contexts are
        omitted.
        """
        found: list[int] = []

        for match in self._CONTEXT_PATTERN.finditer(content):
            ctx = match.group("ctx")
            days_str = match.group("days")

            # The context must contain a return-related verb …
            if not self._RETURN_VERBS.search(ctx):
                continue

            # … and must NOT be dominated by an exclusion signal.
            if self._EXCLUDED_VERBS.search(ctx):
                continue

            found.append(int(days_str))

        return found

    def detect(self, documents: list[dict]) -> list[Conflict]:
        """
        Scan *documents* for return-window day values and report a
        conflict when two or more documents state different values.

        Note: whether the conflicting documents are *currently
        authoritative* is determined by EvidenceResolver, not here.
        This method reports the raw textual disagreement; it is the
        caller's responsibility to decide whether to escalate.
        """
        # Map: days_value -> list[document_id] that contain that value
        return_windows: dict[int, list[str]] = {}

        for document in documents:
            content = document.get("content", "")
            metadata = document.get("metadata", {})

            document_id = metadata.get(
                "document_id",
                "unknown",
            )

            for days in self._extract_return_window_days(content):
                return_windows.setdefault(days, []).append(document_id)

        # No disagreement — zero or one distinct value found.
        if len(return_windows) <= 1:
            return []

        documents_in_conflict = sorted(
            {
                document_id
                for document_ids in return_windows.values()
                for document_id in document_ids
            }
        )

        values = sorted(return_windows)

        description = (
            "Different return windows were found: "
            + ", ".join(f"{days} days" for days in values)
        )

        return [
            Conflict(
                topic="return_window",
                documents=documents_in_conflict,
                description=description,
            )
        ]
