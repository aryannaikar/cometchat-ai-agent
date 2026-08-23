from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from app.pipeline.rag_pipeline import RAGPipeline

app = FastAPI(
    title="RAG Policy Assistant API",
    description="API for customer support RAG assistant.",
    version="1.0.0",
)

# Global pipeline instance
pipeline = None

@app.on_event("startup")
def startup_event():
    global pipeline
    try:
        pipeline = RAGPipeline()
    except Exception as e:
        print(f"Failed to initialize RAG pipeline: {e}")

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    decision: str
    citations: List[str]
    input_guard_decision: Optional[str] = None
    evidence_guard_decision: Optional[str] = None
    output_guard_decision: Optional[str] = None

@app.get("/health")
def health_check():
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not initialized",
        )
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )
        
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not ready",
        )

    try:
        result = pipeline.run(request.question)
        return AskResponse(
            answer=result.answer,
            decision=result.decision,
            citations=result.citations,
            input_guard_decision=result.input_guard_decision,
            evidence_guard_decision=result.evidence_guard_decision,
            output_guard_decision=result.output_guard_decision,
        )
    except Exception as e:
        # Catch unexpected infrastructure/API failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}"
        )
