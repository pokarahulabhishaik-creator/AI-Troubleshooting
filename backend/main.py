"""FastAPI Backend Application for AI Troubleshooting Assistant.

Exposes REST API endpoints for error diagnosis, RAG-powered knowledge retrieval,
and system health monitoring.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.models.schemas import (
    TroubleshootRequest,
    TroubleshootResponse,
    HealthResponse
)
from backend.services.error_classifier import classify_error
from backend.rag.pipeline import run_rag_pipeline
from backend.services.diagnosis import diagnose_error
from backend.services.solution_generator import generate_solution
from backend.rag.embeddings import (
    get_chroma_client,
    get_knowledge_collection,
    build_vector_database,
    COLLECTION_NAME
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to ensure ChromaDB has indexed knowledge on startup."""
    try:
        client = get_chroma_client()
        collection = get_knowledge_collection(client=client)
        if collection.count() == 0:
            print("[Startup] Knowledge collection is empty. Auto-indexing data files...")
            build_vector_database()
        else:
            print(f"[Startup] Vector collection '{COLLECTION_NAME}' active with {collection.count()} chunks.")
    except Exception as exc:
        print(f"[Startup Warning] Could not verify vector database: {exc}")
    yield


app = FastAPI(
    title="AI Troubleshooting Assistant API",
    description="LLM + RAG based Technical Troubleshooting Assistant Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Streamlit development and deployed Streamlit Cloud
import os
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
custom_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
default_origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
]
allowed_origins = list(set(default_origins + custom_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://.*\.streamlit\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", summary="Root Endpoint")
def read_root():
    """Root endpoint returning API status message."""
    return {"message": "AI Troubleshooting Assistant API is running"}


@app.get("/health", response_model=HealthResponse, summary="System Health Check")
def health_check():
    """Returns vector database status and item count."""
    try:
        client = get_chroma_client()
        collection = get_knowledge_collection(client=client)
        count = collection.count()
        return HealthResponse(
            status="ok",
            knowledge_base_count=count,
            collection_name=COLLECTION_NAME,
            version="1.0.0"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(exc)}"
        )


@app.post(
    "/troubleshoot",
    response_model=TroubleshootResponse,
    summary="Diagnose Technical Error"
)
def troubleshoot_error(request: TroubleshootRequest):
    """Diagnoses an error using Error Classifier, RAG Retrieval, Diagnosis, and Solution Generator.

    Processing Flow:
    1. Error Classifier: Identify error type and domain category.
    2. RAG Pipeline: Retrieve relevant context chunks from ChromaDB.
    3. Diagnosis: Synthesize likely causes and evidence.
    4. Solution Generator: Generate step-by-step resolution.
    """
    clean_error = request.error_text.strip()
    if not clean_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="error_text cannot be empty."
        )

    try:
        # Step 1: Error Classifier
        classification = classify_error(clean_error)

        # Step 2: RAG Pipeline Retrieval
        pipeline_output = run_rag_pipeline(query=clean_error, top_k=request.top_k)
        retrieved_docs = pipeline_output.get("results", [])

        # Step 3: Diagnosis
        diagnosis = diagnose_error(
            error_text=clean_error,
            classification=classification,
            retrieved_documents=retrieved_docs
        )

        # Step 4: Solution Generator
        solution = generate_solution(
            error_text=clean_error,
            classification=classification,
            diagnosis=diagnosis,
            retrieved_documents=retrieved_docs
        )

        # Step 5: Format response
        return TroubleshootResponse(
            error_text=clean_error,
            error_type=classification.get("error_type", "UnknownError"),
            category=classification.get("category", "General"),
            confidence=classification.get("confidence", 0.0),
            diagnosis=diagnosis.get("summary", ""),
            likely_causes=diagnosis.get("likely_causes", []),
            solution=solution,
            retrieved_sources=retrieved_docs
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Troubleshooting processing failed: {str(exc)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
