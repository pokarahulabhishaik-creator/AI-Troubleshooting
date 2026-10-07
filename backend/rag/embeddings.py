"""Embeddings and Vector Database Storage Module.

Generates dense embeddings using sentence-transformers (all-MiniLM-L6-v2)
and manages persistence with ChromaDB.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import os
# Limit PyTorch and BLAS memory overhead on 512MB free cloud containers
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
try:
    import torch
    torch.set_num_threads(1)
except Exception:
    pass

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()


def get_project_root() -> Path:
    """Returns the project root directory anchored to this file location."""
    return Path(__file__).resolve().parent.parent.parent


VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "vectorstore")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "troubleshooting_knowledge")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Global singleton caches
_MODEL_INSTANCE: Optional[SentenceTransformer] = None
_CHROMA_CLIENT: Optional[chromadb.PersistentClient] = None
_COLLECTIONS: Dict[str, chromadb.Collection] = {}


def get_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    """Loads and caches the SentenceTransformer model singleton.

    Args:
        model_name: Name of the HuggingFace model. Defaults to 'all-MiniLM-L6-v2'.

    Returns:
        SentenceTransformer instance.
    """
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = SentenceTransformer(model_name)
    return _MODEL_INSTANCE


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generates embedding vectors for a list of string texts with torch inference optimizations.

    Args:
        texts: List of strings to encode.

    Returns:
        List of embedding float vectors.
    """
    if not texts:
        return []
    import torch
    model = get_embedding_model()
    with torch.inference_mode():
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=32)
    return embeddings.tolist()


def get_chroma_client(persist_dir: str = VECTORSTORE_DIR) -> chromadb.PersistentClient:
    """Creates or returns the cached ChromaDB PersistentClient singleton.

    Args:
        persist_dir: Path string to the persistence folder.

    Returns:
        chromadb.PersistentClient instance.
    """
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        path = Path(persist_dir)
        if not path.is_absolute():
            path = get_project_root() / persist_dir
        path.mkdir(parents=True, exist_ok=True)

        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=str(path),
            settings=Settings(anonymized_telemetry=False)
        )
    return _CHROMA_CLIENT


def get_knowledge_collection(
    client: Optional[chromadb.PersistentClient] = None,
    collection_name: str = COLLECTION_NAME
) -> chromadb.Collection:
    """Retrieves or creates the cached Chroma collection for troubleshooting knowledge.

    Args:
        client: Optional PersistentClient. If None, initializes cached client.
        collection_name: Name of collection.

    Returns:
        Chroma collection object.
    """
    global _COLLECTIONS
    if collection_name in _COLLECTIONS:
        return _COLLECTIONS[collection_name]

    if client is None:
        client = get_chroma_client()

    col = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    _COLLECTIONS[collection_name] = col
    return col


def store_document_chunks(
    chunks: List[Dict[str, Any]],
    client: Optional[chromadb.PersistentClient] = None,
    collection_name: str = COLLECTION_NAME
) -> int:
    """Encodes and stores document chunks in ChromaDB with metadata and stable IDs.

    Uses collection.upsert to prevent uncontrolled duplicates on re-runs.

    Args:
        chunks: List of chunk dictionaries containing 'content', 'source', 'category', 'chunk_id'.
        client: Optional PersistentClient.
        collection_name: Name of Chroma collection.

    Returns:
        Number of chunks stored or updated.
    """
    if not chunks:
        return 0

    collection = get_knowledge_collection(client, collection_name=collection_name)

    texts = [c["content"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"source": c["source"], "category": c["category"]} for c in chunks]

    # Generate embeddings
    embeddings = generate_embeddings(texts)

    # Upsert in batches of 100 to avoid payload size constraints
    batch_size = 100
    total_stored = 0

    for i in range(0, len(chunks), batch_size):
        end = i + batch_size
        collection.upsert(
            ids=ids[i:end],
            documents=texts[i:end],
            embeddings=embeddings[i:end],
            metadatas=metadatas[i:end]
        )
        total_stored += len(ids[i:end])

    return total_stored


def build_vector_database(data_dir: str = "data") -> int:
    """End-to-end ingestion pipeline: loads, chunks, and persists knowledge to ChromaDB.

    Args:
        data_dir: Directory containing knowledge files.

    Returns:
        Total number of chunks indexed.
    """
    from backend.rag.ingestion import load_knowledge_documents
    from backend.rag.chunking import chunk_documents

    print(f"[Build VectorDB] Reading knowledge documents from '{data_dir}'...")
    docs = load_knowledge_documents(data_dir=data_dir)
    print(f"[Build VectorDB] Loaded {len(docs)} documents.")

    print("[Build VectorDB] Splitting documents into chunks...")
    chunks = chunk_documents(docs)
    print(f"[Build VectorDB] Generated {len(chunks)} chunks.")

    print(f"[Build VectorDB] Storing into ChromaDB collection '{COLLECTION_NAME}'...")
    stored = store_document_chunks(chunks)
    print(f"[Build VectorDB] Successfully stored {stored} chunks.")
    return stored


if __name__ == "__main__":
    count = build_vector_database()
    print(f"Vector database initialization complete. Total chunks indexed: {count}")
