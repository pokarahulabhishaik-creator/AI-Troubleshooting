"""RAG Pipeline Module for AI Troubleshooting Assistant.

Coordinates query validation and knowledge document retrieval.
"""

from typing import Dict, Any, List
from backend.rag.retriever import retrieve_documents


def run_rag_pipeline(
    query: str,
    top_k: int = 3
) -> Dict[str, Any]:
    """Validates query and retrieves relevant knowledge documents via RAG.

    Args:
        query: User error or query text.
        top_k: Number of relevant context chunks to fetch (default: 3).

    Returns:
        Dictionary containing:
        - 'query': str
        - 'results': List of retrieved document dictionaries
        - 'count': int
    """
    if not query or not isinstance(query, str) or not query.strip():
        return {
            "query": query or "",
            "results": [],
            "count": 0
        }

    clean_query = query.strip()
    safe_top_k = top_k if isinstance(top_k, int) and top_k > 0 else 3

    retrieved: List[Dict[str, Any]] = retrieve_documents(
        query=clean_query,
        top_k=safe_top_k
    )

    return {
        "query": clean_query,
        "results": retrieved,
        "count": len(retrieved)
    }


if __name__ == "__main__":
    out = run_rag_pipeline("ModuleNotFoundError: No module named 'backend'", top_k=2)
    print(f"RAG Pipeline retrieved {out['count']} results.")
