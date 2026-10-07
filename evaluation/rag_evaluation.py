"""RAG Evaluation Module for AI Troubleshooting Assistant.

Evaluates semantic retrieval accuracy, hit rates, and relevance distances
across standard technical error scenarios against ChromaDB knowledge store.
"""

from typing import List, Dict, Any
import time
from backend.rag.pipeline import run_rag_pipeline


# Ground truth evaluation dataset
BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "query": "ModuleNotFoundError: No module named 'backend'",
        "expected_keywords": ["modulenotfounderror", "sys.path", "working directory", "package", "backend"],
        "expected_domain": "Python / Import"
    },
    {
        "id": "Q2",
        "query": "ImportError: cannot import name 'retriever' from partially initialized module",
        "expected_keywords": ["importerror", "circular", "partially initialized", "import"],
        "expected_domain": "Python / Circular Import"
    },
    {
        "id": "Q3",
        "query": "FileNotFoundError: [Errno 2] No such file or directory: 'data/guide.md'",
        "expected_keywords": ["filenotfounderror", "path", "directory", "pathlib"],
        "expected_domain": "File / System"
    },
    {
        "id": "Q4",
        "query": "FastAPI uvicorn error [Errno 10048] address already in use port 8000",
        "expected_keywords": ["10048", "address already in use", "port", "uvicorn", "fastapi"],
        "expected_domain": "FastAPI / Networking"
    },
    {
        "id": "Q5",
        "query": "Streamlit error StreamlitAPIException duplicate key or session state",
        "expected_keywords": ["streamlit", "key", "widget", "session_state"],
        "expected_domain": "Streamlit / UI"
    },
    {
        "id": "Q6",
        "query": "ChromaDB vectorstore error InvalidDimensionException or sqlite3 version",
        "expected_keywords": ["chromadb", "dimension", "sqlite", "collection", "vector"],
        "expected_domain": "Database / Vectorstore"
    },
]


def evaluate_rag_retrieval(top_k: int = 3) -> Dict[str, Any]:
    """Runs benchmark queries through the RAG pipeline and computes retrieval metrics.

    Args:
        top_k: Number of retrieved chunks to inspect per query.

    Returns:
        Dictionary of aggregate evaluation metrics and individual query results.
    """
    results: List[Dict[str, Any]] = []
    total_queries = len(BENCHMARK_QUERIES)
    hits_at_1 = 0
    hits_at_k = 0
    all_distances: List[float] = []

    print("\n" + "=" * 75)
    print("           AI TROUBLESHOOTING ASSISTANT - RAG RETRIEVAL BENCHMARK           ")
    print("=" * 75)

    start_time = time.time()

    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        query_text = item["query"]
        expected_kws = item["expected_keywords"]

        rag_output = run_rag_pipeline(query_text, top_k=top_k)
        retrieved_docs = rag_output.get("results", [])

        # Evaluate Hit@1 and Hit@K
        hit_k = False
        hit_1 = False
        distances = []

        for rank, doc in enumerate(retrieved_docs):
            content_lower = doc.get("content", "").lower()
            source_lower = doc.get("source", "").lower()
            dist = doc.get("distance", 1.0)
            distances.append(dist)
            all_distances.append(dist)

            # Check if any expected keyword matched in source or content
            match_found = any(kw.lower() in content_lower or kw.lower() in source_lower for kw in expected_kws)
            if match_found:
                hit_k = True
                if rank == 0:
                    hit_1 = True

        if hit_1:
            hits_at_1 += 1
        if hit_k:
            hits_at_k += 1

        top_source = retrieved_docs[0]["source"] if retrieved_docs else "None"
        avg_dist = sum(distances) / len(distances) if distances else 0.0

        results.append({
            "id": q_id,
            "query": query_text,
            "domain": item["expected_domain"],
            "retrieved_count": len(retrieved_docs),
            "hit_at_1": hit_1,
            "hit_at_k": hit_k,
            "top_source": top_source,
            "avg_distance": round(avg_dist, 4)
        })

    elapsed = round(time.time() - start_time, 2)
    accuracy_pct = round((hits_at_k / total_queries) * 100, 1)
    hit1_pct = round((hits_at_1 / total_queries) * 100, 1)
    mean_dist = round(sum(all_distances) / len(all_distances), 4) if all_distances else 0.0

    # Display Query Results Table
    print(f"\n{'ID':<4} | {'Domain':<24} | {'Hit@1':<6} | {'Hit@K':<6} | {'Avg Dist':<9} | {'Top Source'}")
    print("-" * 75)
    for r in results:
        h1 = "YES" if r["hit_at_1"] else "NO"
        hk = "YES" if r["hit_at_k"] else "NO"
        src = r["top_source"]
        if len(src) > 30:
            src = "..." + src[-27:]
        print(f"{r['id']:<4} | {r['domain']:<24} | {h1:<6} | {hk:<6} | {r['avg_distance']:<9} | {src}")

    # Display Aggregate Summary
    print("=" * 75)
    print("                       AGGREGATE EVALUATION METRICS                         ")
    print("=" * 75)
    print(f"Total Benchmark Queries      : {total_queries}")
    print(f"Top-K Parameter Evaluated    : {top_k}")
    print(f"Hit@1 Retrieval Rate         : {hits_at_1}/{total_queries} ({hit1_pct}%)")
    print(f"Hit@K Retrieval Accuracy     : {hits_at_k}/{total_queries} ({accuracy_pct}%)")
    print(f"Mean Semantic Cosine Distance: {mean_dist} (Lower indicates closer relevance)")
    print(f"Total Benchmark Execution Time: {elapsed}s")
    print("=" * 75 + "\n")

    return {
        "total_queries": total_queries,
        "hits_at_1": hits_at_1,
        "hits_at_k": hits_at_k,
        "accuracy_pct": accuracy_pct,
        "hit1_pct": hit1_pct,
        "mean_cosine_distance": mean_dist,
        "elapsed_seconds": elapsed,
        "details": results
    }


if __name__ == "__main__":
    evaluate_rag_retrieval(top_k=3)
