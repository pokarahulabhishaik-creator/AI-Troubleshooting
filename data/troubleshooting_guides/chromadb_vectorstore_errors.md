# Troubleshooting ChromaDB Vector Database Errors

## Overview
ChromaDB is an open-source vector store for embeddings. Typical problems involve SQLite library version requirements, collection persistence directory conflicts, embedding dimensionality mismatches, and lock contention.

## Common Error Signatures
- `RuntimeError: Your system has an unsupported version of sqlite3. Chroma requires sqlite3 >= 3.35.0.`
- `ValueError: Collection troubleshooting_knowledge does not exist.`
- `InvalidDimensionException: Embedding dimension 384 does not match collection dimension 1536.`
- `sqlite3.OperationalError: database is locked`

## Common Causes
1. **Outdated System SQLite**: Older Linux or Windows environments bundling SQLite versions below 3.35.0.
2. **Dimension Mismatch**: Adding vectors with a different embedding dimension (e.g., mixing OpenAI text-embedding-ada-002 with 1536 dimensions and all-MiniLM-L6-v2 with 384 dimensions) into the same collection.
3. **Uninitialized Vectorstore**: Querying ChromaDB before running the document ingestion and embedding indexing process.
4. **Duplicate Document IDs**: Calling `collection.add()` with non-unique IDs without handling updates or checking for existing keys.
5. **Concurrent Database Locks**: Multiple processes trying to write concurrently to a single SQLite-backed `PersistentClient` path.

## Step-by-Step Resolution

### 1. Handling SQLite Version Requirements
On systems with outdated SQLite, install `pysqlite3-binary` and swap the sys module before importing chromadb:
```python
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
```
(On modern Windows Python 3.10+, SQLite 3.37+ is bundled by default and does not require this workaround.)

### 2. Standardize Embedding Dimension
Use consistent embedding models across ingestion and retrieval:
- `all-MiniLM-L6-v2` produces vectors of dimension `384`.
- Never query an `all-MiniLM-L6-v2` collection with default Chroma embeddings or OpenAI embeddings without clearing or creating a separate collection.

### 3. Use chromadb.PersistentClient with get_or_create_collection
Always use persistent clients and idempotent collection creation:
```python
import chromadb

client = chromadb.PersistentClient(path="vectorstore")
collection = client.get_or_create_collection(
    name="troubleshooting_knowledge",
    metadata={"hnsw:space": "cosine"}
)
```

### 4. Use Upsert Instead of Add to Prevent ID Collisions
```python
collection.upsert(
    documents=chunk_texts,
    embeddings=chunk_embeddings,
    metadatas=chunk_metadatas,
    ids=chunk_ids
)
```

## Verification Steps
Query collection count:
```python
import chromadb
client = chromadb.PersistentClient(path="vectorstore")
col = client.get_collection("troubleshooting_knowledge")
print("Total vectors indexed:", col.count())
```
