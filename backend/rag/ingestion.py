"""Document Ingestion Module for AI Troubleshooting Assistant.

Reads .txt and .md technical knowledge documents from the data directory,
extracts document content, source file paths, and category metadata.
"""

from pathlib import Path
from typing import List, Dict, Any, Union


def get_project_root() -> Path:
    """Returns the project root directory anchored to this file location."""
    return Path(__file__).resolve().parent.parent.parent


def load_knowledge_documents(data_dir: Union[str, Path] = "data") -> List[Dict[str, Any]]:
    """Recursively scans data_dir for .txt and .md files and returns structured documents.

    Each document dictionary contains:
    - 'content': Raw string text of the file
    - 'source': Relative or canonical path string of the source file
    - 'category': Subdirectory name under data/ (e.g., 'troubleshooting_guides', 'faqs')

    Args:
        data_dir: Path to the data directory (relative or absolute).

    Returns:
        List of structured document dictionaries.
    """
    path = Path(data_dir)
    if not path.is_absolute():
        # Check relative to current working directory first, then project root
        if not path.exists():
            path = get_project_root() / data_dir

    if not path.exists() or not path.is_dir():
        print(f"[Warning] Knowledge directory does not exist: {path}")
        return []

    documents: List[Dict[str, Any]] = []
    # Supported file extensions
    supported_extensions = {".md", ".txt"}

    for file_path in path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue

                # Category is determined by the immediate subdirectory inside data/
                try:
                    rel_to_data = file_path.relative_to(path)
                    category = rel_to_data.parts[0] if len(rel_to_data.parts) > 1 else "general"
                except ValueError:
                    category = file_path.parent.name or "general"

                # Store normalized source path
                try:
                    source_str = str(file_path.relative_to(get_project_root())).replace("\\", "/")
                except ValueError:
                    source_str = str(file_path).replace("\\", "/")

                documents.append({
                    "content": content,
                    "source": source_str,
                    "category": category
                })
            except Exception as exc:
                print(f"[Error] Failed to read {file_path}: {exc}")

    return documents


if __name__ == "__main__":
    docs = load_knowledge_documents()
    print(f"Loaded {len(docs)} documents successfully.")
    for idx, doc in enumerate(docs[:3], 1):
        print(f"[{idx}] Source: {doc['source']} | Category: {doc['category']} | Length: {len(doc['content'])} chars")
