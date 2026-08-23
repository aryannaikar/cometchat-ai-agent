# Aster & Row Policy Assistant

## 1. Project Title
**Aster & Row Customer Policy Assistant** — An Evidence-Grounded RAG Policy System

## 2. Project Overview
The Aster & Row Policy Assistant is a production-grade, evidence-grounded Retrieval-Augmented Generation (RAG) system built to answer customer support queries accurately regarding return windows, defective items, gift cards, and membership privileges. The system uses strict guardrails and deterministic reasoning to prevent hallucinations, correctly resolve document conflicts (e.g. active vs. superseded policies), and safely abstain when reliable policy evidence is unavailable.

## 3. Key Features
- **Deterministic Numerical Reasoning**: Mathematical comparisons (e.g., comparing user-provided days against policy limits) are evaluated outside the LLM to prevent arithmetic hallucinations.
- **Multi-Stage Guard Architecture**: Employs Input Guards, Retrieval Evidence Guards, and Output Guards to guarantee safety and citation accuracy.
- **Evidence Resolution & Conflict Detection**: Aggressively filters out superseded policy documents and internal drafts, and flags active contradictions for human review.
- **Safe Abstention Mechanism**: Intercepts ungrounded queries (e.g. "How do I cook a turkey?") and safely abstains instead of inventing answers.
- **Enterprise UI & REST API**: Exposed via a high-performance FastAPI backend connected to a modern, responsive React frontend.

## 4. Architecture
```
React Frontend
      ↓ HTTP (POST /api/query)
FastAPI Backend
      ↓
Input Guard
      ↓
Retriever (ChromaDB + sentence-transformers)
      ↓
Evidence Resolver (Authority & Conflict Filtering)
      ↓
Evidence Guard (Semantic Overlap Verification)
      ↓
Policy Decision Layer (Deterministic Math Check)
      ↓
Answer Generator (NVIDIA Llama-3.1-8B)
      ↓
Output Guard (Claim & Numerical Verification)
      ↓
JSON Response (Answer + Citations + Guard Statuses)
```

## 5. RAG Pipeline
1. **User Question**: Input submitted via CLI, API, or React interface.
2. **Input Guard**: Validates question format and checks for prompt injection or policy manipulation attempts.
3. **Vector Retrieval**: Retrieves top candidate chunks from ChromaDB using `all-MiniLM-L6-v2` embeddings.
4. **Evidence Resolution**: Classifies documents into authoritative (active), historical (superseded), or non-authoritative (draft). Detects conflicts across active policies.
5. **Evidence Guard**: Verifies semantic relevance between the query and retrieved evidence. Triggers `ABSTAIN` if overlap is insufficient.
6. **Policy Decision Layer**: Evaluates numerical boundaries (e.g., standard 30-day window vs. 7-day reporting window) deterministically.
7. **Answer Generation**: Generates grounded, concise answers using NVIDIA's `meta/llama-3.1-8b-instruct` model constrained strictly by evidence.
8. **Output Guard**: Ensures no unsupported numeric claims or ungrounded statements are present in the output.
9. **Final Response**: Returns structured answer, citations, and guard statuses.

## 6. Guard Architecture
- **Input Guard**: Rejects empty queries, whitespace, and prompt injection patterns.
- **Evidence Guard**: Enforces semantic overlap to block out-of-domain queries.
- **Output Guard**: Whitelists user-provided values and verifies LLM numeric claims against policy evidence.

## 7. Frontend
- Built with React 18, Vite, and Lucide React icons.
- Displays message cards with collapsible **Verification details** (Input, Evidence, Output guard statuses) and structured source citations.
- Includes quick-start example questions, loading animations, error fallbacks, and full mobile/desktop responsiveness.

## 8. FastAPI Backend
- Asynchronous FastAPI server (`backend/main.py`) wrapping the core pipeline.
- Configured with CORS middleware to allow secure local development with the Vite frontend.
- Exposes OpenAPI documentation automatically at `/docs`.

## 9. Tech Stack
- **Backend & AI Core**: Python 3.13, FastAPI, Uvicorn, Pydantic, ChromaDB, Sentence-Transformers, OpenAI SDK (NVIDIA API client).
- **Frontend**: Node.js, React 18, Vite, Lucide-React, Vanilla CSS.
- **Testing**: Pytest.

## 10. Project Structure
```
ai-agent-intern-test/
├── app/
│   ├── api/             # Legacy FastAPI endpoints
│   ├── pipeline/        # Central RAGPipeline orchestrator
│   └── rag/             # Core RAG components (Retriever, VectorStore, Guards, Generator)
├── backend/
│   └── main.py          # Production FastAPI application
├── data/                # Knowledge base markdown files
├── frontend/            # React (Vite) frontend application
│   ├── src/
│   │   ├── components/  # Header, EmptyState, MessageBubble, ChatInput, ChatWindow
│   │   ├── services/    # API client service (api.js)
│   │   └── styles/      # Modular component styling
│   └── package.json
├── tests/               # 52 unit and integration tests
├── test_rag.py          # Interactive CLI test script
├── requirements.txt     # Python dependencies
└── README.md
```

## 11. Environment Variables
Create a `.env` file in the root directory:
```env
NVIDIA_API_KEY=your_nvidia_api_key_here
HF_TOKEN=your_optional_huggingface_token
```
*Note: Secrets are kept server-side and never exposed to the React frontend.*

## 12. Installation

1. Navigate to the repository root:
```bash
cd ai-agent-intern-test
```

2. Create and activate a Python virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Frontend dependencies:
```bash
cd frontend
npm install
cd ..
```

## 13. How to Run Backend
From the root directory with `.venv` activated:
```bash
.venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000
```
The API server will start on `http://localhost:8000`.

## 14. How to Run Frontend
From the `frontend/` directory:
```bash
cd frontend
npm run dev
```
The application will be accessible at `http://localhost:5173`.

## 15. API Endpoint Documentation
- **`GET /api/health`**: Health check verifying the backend process status.
- **`POST /api/query`**: Primary RAG pipeline query endpoint.

## 16. Example Request
```json
POST /api/query
Content-Type: application/json

{
  "question": "Can I return my shoes after 20 days?"
}
```

## 17. Example Response
```json
{
  "answer": "Based on the provided policy, your request to return the shoes after 20 days is within the policy window. The standard return window allows returns within 30 calendar days of delivery.",
  "decision": "answer",
  "citations": [
    "01-returns-policy-current.md — Knowledge base"
  ],
  "input_guard_decision": "allow",
  "evidence_guard_decision": "allow",
  "output_guard_decision": "allow"
}
```

## 18. Guard Behavior
- **`ALLOW`**: Query passed safety checks and generated an evidence-supported answer.
- **`REJECT`**: Query violated safety checks (e.g. empty input or prompt injection).
- **`ABSTAIN`**: System halted generation due to insufficient or irrelevant evidence.
- **`HUMAN_HANDOFF`**: System detected conflicting active authoritative policies requiring human review.

## 19. Abstention Behavior
When a user asks a question outside the scope of Aster & Row policies (e.g., *"How do I cook a turkey?"*), the `EvidenceGuard` identifies zero semantic relevance in the retrieved chunks and forces an `ABSTAIN` decision. The assistant responds with:
> *"I don't have enough reliable information in the available documents to answer this question."*

## 20. Citation Behavior
Citations are generated deterministically from the authoritative evidence selected during resolution. Only documents directly supporting the answer are cited, avoiding noise from candidate retrieval.

## 21. Testing
Run the comprehensive Pytest suite:
```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
Run the interactive CLI test script:
```bash
.venv\Scripts\python.exe test_rag.py
```

## 22. Known Limitations
- **Order Lookup Integration**: The `orders.json` lookup utility is not yet integrated into the `/api/query` API endpoint.
- **Stateless Sessions**: Multi-turn conversation context is stateless across individual `/api/query` calls.
