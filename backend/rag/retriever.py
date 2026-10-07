"""Document Retrieval Module for AI Troubleshooting Assistant.

Queries the ChromaDB vector database using semantic similarity search.
"""

from typing import List, Dict, Any, Optional
from backend.rag.embeddings import (
    get_chroma_client,
    get_knowledge_collection,
    generate_embeddings,
    COLLECTION_NAME
)


# In-memory query cache for instant responses on identical queries
_RETRIEVAL_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def retrieve_documents(
    query: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """Retrieves the top_k most relevant documents from ChromaDB for a given query.

    Args:
        query: User technical error or question string.
        top_k: Number of relevant chunks to retrieve (default: 3).

    Returns:
        List of dictionaries with keys:
        - 'content': str
        - 'source': str
        - 'category': str
        - 'distance': float (cosine distance, smaller = closer)
    """
    if not query or not isinstance(query, str) or not query.strip():
        return []

    clean_q = query.strip()
    cache_key = f"{clean_q}__k_{top_k}"
    if cache_key in _RETRIEVAL_CACHE:
        return _RETRIEVAL_CACHE[cache_key]

    # Validate and constrain top_k
    if not isinstance(top_k, int) or top_k <= 0:
        top_k = 3
    top_k = min(top_k, 20)

    try:
        collection = get_knowledge_collection(collection_name=COLLECTION_NAME)

        total_items = collection.count()
        if total_items == 0:
            print("[Retriever Warning] Knowledge collection is empty. Run ingestion first.")
            return []

        # Generate query embedding
        query_embeddings = generate_embeddings([query.strip()])
        if not query_embeddings or len(query_embeddings) == 0:
            print("[Retriever Error] Failed to generate embedding for query.")
            return []

        n_results = min(top_k, total_items)

        # Query ChromaDB
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        retrieved: List[Dict[str, Any]] = []

        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for i in range(len(docs)):
                doc_content = docs[i]
                meta = metas[i] if i < len(metas) and metas[i] else {}
                dist = dists[i] if i < len(dists) and dists[i] is not None else 0.0

                retrieved.append({
                    "content": doc_content,
                    "source": meta.get("source", "unknown"),
                    "category": meta.get("category", "general"),
                    "distance": round(float(dist), 4)
                })

        if retrieved:
            _RETRIEVAL_CACHE[cache_key] = retrieved

        return retrieved

    except Exception as exc:
        print(f"[Retriever Error] Exception during document retrieval: {exc}")
        return []


if __name__ == "__main__":
    test_query = "ModuleNotFoundError: No module named 'backend'"
    docs = retrieve_documents(test_query, top_k=2)
    print(f"Retrieved {len(docs)} documents for query: {test_query}")
    for d in docs:
        print(f"Source: {d['source']} | Distance: {d['distance']}")
        print(f"Content: {d['content'][:120]}...\n")
