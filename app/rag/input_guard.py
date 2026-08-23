import re
from dataclasses import dataclass
from enum import Enum


class InputDecision(str, Enum):
    ALLOW = "allow"
    REJECT = "reject"


@dataclass(frozen=True)
class InputGuardResult:
    decision: InputDecision
    reason: str


def validate_question(question: str) -> bool:
    if not question or not question.strip():
        return False
    return True

class InputGuard:
    """
    Validates user queries before they enter the RAG pipeline.
    
    Ensures queries are not empty, excessively long, or attempting
    prompt injection/policy manipulation.
    """
    
    # Maximum length for a legitimate customer question
    MAX_LENGTH = 500
    
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(the\s+)?policy",
        r"ignore\s+(the\s+)?retrieved\s+evidence",
        r"ignore\s+(the\s+)?authoritative\s+documents",
        r"ignore\s+(the\s+)?documents",
        r"forget\s+(the\s+)?system\s+instructions",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"show\s+(me\s+your\s+)?hidden\s+instructions",
        r"tell\s+me\s+the\s+instructions",
        r"pretend\s+(the\s+)?policy\s+says",
        r"change\s+(the\s+)?return\s+policy",
        r"assume\s+(the\s+)?return\s+window",
        r"override\s+(the\s+)?retrieved\s+policy",
        r"treat\s+(the\s+)?superseded\s+policy",
        r"own\s+knowledge"
    ]

    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def check(self, question: str) -> InputGuardResult:
        if not validate_question(question):
            return InputGuardResult(
                decision=InputDecision.REJECT,
                reason="Query is empty or whitespace."
            )
            
        if len(question) > self.MAX_LENGTH:
            return InputGuardResult(
                decision=InputDecision.REJECT,
                reason=f"Query exceeds maximum length of {self.MAX_LENGTH} characters."
            )
            
        for pattern in self._patterns:
            if pattern.search(question):
                return InputGuardResult(
                    decision=InputDecision.REJECT,
                    reason="The query contains a prompt injection attempt."
                )
                
        return InputGuardResult(
            decision=InputDecision.ALLOW,
            reason="Query is valid."
        )
