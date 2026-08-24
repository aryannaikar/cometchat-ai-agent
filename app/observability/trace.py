import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

LOG_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(LOG_DIR, "trace.log")

# Ensure directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Set up standard logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGPipeline")

def log_trace(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    resolved_question: Optional[str] = None,
    retrieved_passages: Optional[List[Dict[str, Any]]] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    tool_results: Optional[List[Dict[str, Any]]] = None,
    final_response: Optional[str] = None,
    decision: Optional[str] = None,
    errors: Optional[List[str]] = None,
    handoff_recommended: bool = False,
    input_guard_decision: Optional[str] = None,
    evidence_guard_decision: Optional[str] = None,
    output_guard_decision: Optional[str] = None,
):
    """Logs structured trace details for observability."""
    trace_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "question": question,
        "history": history or [],
        "resolved_question": resolved_question or question,
        "retrieved_passages": [
            {
                "document_id": p.get("metadata", {}).get("document_id"),
                "filename": p.get("metadata", {}).get("filename"),
                "heading": p.get("metadata", {}).get("heading"),
                "score": p.get("score"),
                "status": p.get("metadata", {}).get("status")
            }
            for p in (retrieved_passages or [])
        ],
        "tool_calls": tool_calls or [],
        "tool_results": tool_results or [],
        "final_response": final_response,
        "decision": decision,
        "errors": errors or [],
        "handoff_recommended": handoff_recommended,
        "guards": {
            "input_guard": input_guard_decision,
            "evidence_guard": evidence_guard_decision,
            "output_guard": output_guard_decision
        }
    }
    
    # Write to local JSON lines file
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_data) + "\n")
    except Exception as e:
        logger.error(f"Failed to write to trace log file: {e}")
        
    # Also log to console for debugging
    logger.info(f"--- RAG TRACE ---")
    logger.info(f"Question: {question}")
    if resolved_question and resolved_question != question:
        logger.info(f"Resolved Question: {resolved_question}")
    logger.info(f"Decision: {decision} | Handoff: {handoff_recommended}")
    if tool_calls:
        logger.info(f"Tool Calls: {tool_calls}")
    if errors:
        logger.error(f"Errors: {errors}")
    logger.info(f"-----------------")
