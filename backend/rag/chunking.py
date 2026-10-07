"""Document Chunking Module for AI Troubleshooting Assistant.

Splits documents into overlapping chunks with metadata preservation.
"""

from typing import List, Dict, Any

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """Splits raw text into overlapping string chunks.

    Args:
        text: The source text to split.
        chunk_size: Maximum character length for each chunk.
        chunk_overlap: Number of overlapping characters between adjacent chunks.

    Returns:
        List of text chunks.

    Raises:
        ValueError: If chunk_overlap is greater than or equal to chunk_size,
                    or if chunk_size is non-positive.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if chunk_overlap < 0:
        raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
        )

    clean_text = text.strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [clean_text]

    chunks: List[str] = []
    step = chunk_size - chunk_overlap
    start = 0
    text_len = len(clean_text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += step

    return chunks


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """Chunks a list of ingested documents while preserving metadata.

    Each returned chunk dictionary contains:
    - 'content': Chunk text
    - 'source': Original source file
    - 'category': Document category
    - 'chunk_id': Stable, unique chunk identifier

    Args:
        documents: List of document dicts with keys 'content', 'source', 'category'.
        chunk_size: Maximum chunk length.
        chunk_overlap: Chunk overlap length.

    Returns:
        List of chunk dictionaries with metadata.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
        )

    all_chunks: List[Dict[str, Any]] = []

    for doc_idx, doc in enumerate(documents):
        content = doc.get("content", "")
        source = doc.get("source", f"doc_{doc_idx}")
        category = doc.get("category", "general")

        text_chunks = chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Generate readable, stable base prefix from source path
        safe_source_prefix = (
            source.replace("/", "_")
            .replace("\\", "_")
            .replace(".", "_")
            .replace(":", "_")
            .strip("_")
        )

        for chunk_idx, chunk_str in enumerate(text_chunks):
            chunk_id = f"{safe_source_prefix}_chk_{chunk_idx:03d}"
            all_chunks.append({
                "content": chunk_str,
                "source": source,
                "category": category,
                "chunk_id": chunk_id
            })

    return all_chunks


if __name__ == "__main__":
    sample_doc = {
        "content": "A" * 1200,
        "source": "data/sample.txt",
        "category": "sample"
    }
    sample_chunks = chunk_documents([sample_doc], chunk_size=500, chunk_overlap=100)
    print(f"Created {len(sample_chunks)} chunks from 1200 char document.")
    for c in sample_chunks:
        print(f"ID: {c['chunk_id']} | Length: {len(c['content'])}")
