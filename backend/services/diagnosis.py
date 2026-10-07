"""Diagnosis Service.

Analyzes the error in conjunction with retrieved knowledge documents to generate
grounded technical causes, diagnostic summaries, and citations of evidence.
"""

from typing import List, Dict, Any
import re


def diagnose_error(
    error_text: str,
    classification: Dict[str, Any],
    retrieved_documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Diagnoses the root cause of an error grounded in retrieved RAG knowledge.

    Args:
        error_text: The user error message or stack trace.
        classification: Output from error_classifier (error_type, category, confidence).
        retrieved_documents: List of retrieved chunks from RAG retriever.

    Returns:
        Dictionary with:
        - 'summary': High-level diagnosis summary string.
        - 'likely_causes': List of probable causes grounded in retrieved knowledge.
        - 'evidence': List of evidence excerpts directly from retrieved documents.
    """
    error_type = classification.get("error_type", "UnknownError")
    category = classification.get("category", "General")

    # Extract target name (e.g. module name, port, or file) from error text if possible
    target_match = re.search(r"['\"]([^'\"]+)['\"]", error_text)
    target_entity = target_match.group(1) if target_match else ""

    evidence_list: List[str] = []
    extracted_causes: List[str] = []

    # Parse evidence and causes from retrieved documents
    for doc in retrieved_documents:
        content = doc.get("content", "")
        source = doc.get("source", "knowledge_base")

        # Find "Common Causes" or bullet points in retrieved text
        causes_section = False
        for line in content.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue

            # Detect headers or bullet lines
            if "cause" in line_str.lower() and (":" in line_str or line_str.startswith("#")):
                causes_section = True
                continue

            if causes_section and (line_str.startswith("-") or re.match(r"^\d+\.", line_str)):
                clean_cause = re.sub(r"^[-*\d.]+\s*", "", line_str)
                # Clean markdown bold markers
                clean_cause = clean_cause.replace("**", "").strip()
                if len(clean_cause) > 10 and clean_cause not in extracted_causes:
                    extracted_causes.append(clean_cause)
                if len(extracted_causes) >= 5:
                    break

        # Capture concise evidence snippets
        first_few_lines = [
            ln.strip() for ln in content.split("\n")
            if ln.strip() and not ln.startswith("#")
        ][:2]
        if first_few_lines:
            snippet = " ".join(first_few_lines)
            if len(snippet) > 160:
                snippet = snippet[:157] + "..."
            evidence_entry = f"[{source}]: \"{snippet}\""
            if evidence_entry not in evidence_list:
                evidence_list.append(evidence_entry)

    # Build domain-specific likely causes if none extracted or to supplement
    if not extracted_causes:
        if error_type == "ModuleNotFoundError":
            extracted_causes = [
                f"Python cannot locate the package '{target_entity or 'module'}' because the current working directory is not the project root.",
                "The virtual environment containing the dependencies is not activated in the current shell.",
                f"The package '{target_entity or 'module'}' has not been installed via pip into the active environment.",
                "The project directory structure is missing proper package boundaries or import paths on sys.path."
            ]
        elif error_type == "ImportError":
            extracted_causes = [
                "Circular import between modules attempting to load each other during initialization.",
                "Local script name shadows a standard library or installed third-party package.",
                "Attempted relative import from a script executed directly without package context."
            ]
        elif error_type == "FileNotFoundError":
            extracted_causes = [
                "Relative file path was evaluated relative to the active working directory rather than the script location.",
                "The specified file or parent directory does not exist or was misspelled.",
                "Path string contains unescaped Windows backslashes causing escape sequence corruption."
            ]
        elif error_type in ("ConnectionError", "ConnectionRefusedError"):
            extracted_causes = [
                "Target server or backend service (e.g., FastAPI on port 8000) is not currently running.",
                "Client is pointing to an incorrect URL, port, or protocol (e.g. http vs https).",
                "Firewall or network security software blocked the local loopback connection."
            ]
        elif "10048" in error_text or "Address already in use" in error_text:
            extracted_causes = [
                "Another process (such as a previous Uvicorn or backend instance) is already listening on the requested port.",
                "Previous server instance did not shut down cleanly and is still bound to the socket."
            ]
        else:
            extracted_causes = [
                f"Configuration or runtime mismatch related to {category} / {error_type}.",
                "Missing environment variables or prerequisite dependencies.",
                "Syntax or parameter type mismatch in application code."
            ]

    # Build concise diagnostic summary
    if error_type == "ModuleNotFoundError" and target_entity:
        summary = (
            f"Python cannot find the '{target_entity}' package because of an incorrect "
            f"working directory, package structure, Python environment, or import path."
        )
    elif error_type == "ImportError":
        summary = (
            f"Python encountered an import initialization failure, likely due to a circular import "
            f"dependency or a shadowed module name."
        )
    elif error_type == "FileNotFoundError":
        summary = (
            f"The operating system could not find the target file or directory due to an invalid relative "
            f"path or missing resource."
        )
    elif error_type in ("ConnectionError", "ConnectionRefusedError"):
        summary = (
            f"The client failed to establish an HTTP connection because the target service "
            f"is offline or refusing connections on the configured port."
        )
    elif "10048" in error_text or "Address already in use" in error_text:
        summary = (
            f"Port collision: The specified socket address is already in use by another running process."
        )
    else:
        summary = (
            f"A {error_type} occurred in the {category} domain during application execution."
        )

    return {
        "summary": summary,
        "likely_causes": extracted_causes[:5],
        "evidence": evidence_list[:3]
    }


if __name__ == "__main__":
    from backend.rag.retriever import retrieve_documents
    sample_err = "ModuleNotFoundError: No module named 'backend'"
    docs = retrieve_documents(sample_err, top_k=2)
    diag = diagnose_error(
        sample_err,
        {"error_type": "ModuleNotFoundError", "category": "Python", "confidence": 0.95},
        docs
    )
    print("Summary:", diag["summary"])
    print("Causes:", diag["likely_causes"])
    print("Evidence:", diag["evidence"])
