from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.pipeline.rag_pipeline import RAGPipeline

app = FastAPI(
    title="RAG Policy Assistant API",
    description="API for Aster & Row customer support RAG assistant.",
    version="1.0.0",
)

# Configure CORS for React frontend (defaulting to localhost:5173 for Vite)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance to avoid reloading vector store / models on every request
pipeline = None

@app.on_event("startup")
def startup_event():
    global pipeline
    try:
        pipeline = RAGPipeline()
    except Exception as e:
        print(f"Failed to initialize RAG pipeline: {e}")

class Message(BaseModel):
    type: str
    text: str

class QueryRequest(BaseModel):
    question: str
    history: Optional[List[Message]] = None

class QueryResponse(BaseModel):
    answer: str
    decision: str
    citations: List[str]
    input_guard_decision: Optional[str] = None
    evidence_guard_decision: Optional[str] = None
    output_guard_decision: Optional[str] = None

@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend status."""
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not initialized",
        )
    return {"status": "ok"}

@app.post("/api/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """
    Query the RAG pipeline with a customer question.
    """
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not ready",
        )

    try:
        history_dicts = None
        if request.history:
            history_dicts = [{"type": msg.type, "text": msg.text} for msg in request.history]
            
        result = pipeline.run(request.question, history=history_dicts)
        
        # If the input guard rejected because it was empty/whitespace, it's a 400 Bad Request
        # (Though we still return it gracefully as a PipelineResult, returning HTTP 400 is also acceptable if strictly empty)
        # But wait, the RAG pipeline natively handles it and returns a clean reject. We will just return the native decision!
        
        return QueryResponse(
            answer=result.answer,
            decision=result.decision,
            citations=result.citations,
            input_guard_decision=result.input_guard_decision,
            evidence_guard_decision=result.evidence_guard_decision,
            output_guard_decision=result.output_guard_decision,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}"
        )
