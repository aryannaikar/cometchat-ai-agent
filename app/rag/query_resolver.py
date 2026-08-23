from app.llm.nvidia_client import NVIDIAClient

class QueryContextResolver:
    """
    Rewrites a follow-up question into a standalone query using conversation history.
    """
    
    def __init__(self, llm_client: NVIDIAClient | None = None):
        self.llm_client = llm_client or NVIDIAClient()
        
    def resolve(self, current_question: str, history: list[dict[str, str]]) -> str:
        """
        Takes the current question and the conversation history and returns a standalone question.
        If there is no history, returns the current question as is.
        """
        if not history or not current_question.strip():
            return current_question
            
        # Format history
        formatted_history = ""
        for msg in history[-4:]: # Only take last 4 messages to avoid blowing up context
            role = "User" if msg["type"] == "user" else "Assistant"
            formatted_history += f"{role}: {msg['text']}\n"
            
        prompt = f"""You are a helpful assistant whose job is to rewrite a user's follow-up question into a standalone question based on the conversation history.

CONVERSATION HISTORY:
{formatted_history}

CURRENT FOLLOW-UP QUESTION:
{current_question}

REWRITE INSTRUCTIONS:
1. Rewrite the CURRENT FOLLOW-UP QUESTION to be fully standalone.
2. IMPORTANT: If the conversation was about a specific condition (e.g., "damaged item", "defective item", "gift card"), you MUST include that condition in the rewritten question.
3. IMPORTANT: If the follow-up changes a value (e.g. from "5 days" to "10 days", or "20 days" to "40 days"), apply the new value but KEEP the subject and its condition (e.g., "damaged item") from the history.
4. DO NOT answer the question. Only rewrite it.
5. Output ONLY the rewritten question string, nothing else.

STANDALONE QUESTION:"""

        try:
            standalone_query = self.llm_client.generate(prompt)
            # Basic fallback if it failed to generate something reasonable
            if not standalone_query or len(standalone_query) > 200:
                return current_question
            return standalone_query
        except Exception:
            return current_question
