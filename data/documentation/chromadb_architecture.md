# ChromaDB Architecture and Troubleshooting Guide

## ChromaDB Vectorstore Overview
ChromaDB is an embedded vector database designed for retrieval-augmented generation (RAG) applications. It manages document embeddings, dense vector similarity indices, and document metadata.

## Core Components
1. **Persistent Client**: Created via `chromadb.PersistentClient(path="vectorstore")`. Saves all collections and SQLite index data to the specified disk path.
2. **Collection**: Logical groupings of vectors, metadata, and raw document chunks. Created or retrieved with `client.get_or_create_collection(name="...")`.
3. **Index Structure**: Chroma uses HNSW (Hierarchical Navigable Small World) graphs for nearest neighbor search, backed by an embedded SQLite database storing document metadata and chunk identifiers.
4. **Distance Metrics**: Supports `cosine`, `l2` (squared euclidean), and `ip` (inner product) distance metrics.

## Common Operations and Pitfalls
- **Collection Initialization**: Attempting to query an uninitialized or empty collection will raise errors or return empty lists. Verify `collection.count() > 0` before querying.
- **Idempotent Ingestion**: Use `collection.upsert()` instead of `collection.add()` when re-running ingestion scripts to prevent duplicate primary key collisions.
- **Embedding Dimensionality**: All vectors added to a collection must share identical vector dimensions. `all-MiniLM-L6-v2` produces 384-dimensional embeddings.
