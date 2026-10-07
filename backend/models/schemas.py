"""Pydantic Models and Data Schemas for AI Troubleshooting Assistant.

Defines request and response structures with validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TroubleshootRequest(BaseModel):
    """Request payload for diagnosing an error."""
    error_text: str = Field(
        ...,
        min_length=1,
        description="The error message, exception name, or stack trace to troubleshoot.",
        examples=["ModuleNotFoundError: No module named 'backend'"]
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of RAG knowledge chunks to retrieve."
    )


class RetrievedSourceItem(BaseModel):
    """Metadata and excerpt of a retrieved knowledge source."""
    source: str = Field(..., description="Source file path.")
    category: str = Field(..., description="Document category.")
    distance: float = Field(..., description="Vector cosine distance to query.")
    content: str = Field(..., description="Text content of the retrieved chunk.")


class TroubleshootResponse(BaseModel):
    """Complete diagnostic and troubleshooting response schema."""
    error_text: str = Field(..., description="Original input error text.")
    error_type: str = Field(..., description="Classified error type.")
    category: str = Field(..., description="Technical domain category.")
    confidence: float = Field(..., description="Classification confidence score between 0.0 and 1.0.")
    diagnosis: str = Field(..., description="Concise diagnostic summary of the error.")
    likely_causes: List[str] = Field(..., description="List of probable root causes.")
    solution: str = Field(..., description="Detailed step-by-step resolution instructions.")
    retrieved_sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Knowledge base sources and chunks used by RAG."
    )


class HealthResponse(BaseModel):
    """System health status response."""
    status: str = Field(..., description="Health status (e.g. 'ok').")
    knowledge_base_count: int = Field(..., description="Number of indexed chunks in ChromaDB.")
    collection_name: str = Field(..., description="Active ChromaDB collection name.")
    version: str = Field(default="1.0.0", description="API version.")
