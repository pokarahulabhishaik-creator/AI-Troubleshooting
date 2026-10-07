"""Error Classifier Service.

Identifies the technical error type and domain category from an error string
or stack trace using robust rule-based pattern matching.
"""

import re
from typing import Dict, Any, Tuple


# Known specific error types and their default domain categories
ERROR_TYPE_PATTERNS = [
    (r"\bModuleNotFoundError\b", "ModuleNotFoundError", "Python"),
    (r"\bImportError\b", "ImportError", "Python"),
    (r"\bFileNotFoundError\b", "FileNotFoundError", "File/System"),
    (r"\bPermissionError\b", "PermissionError", "File/System"),
    (r"\bSyntaxError\b", "SyntaxError", "Python"),
    (r"\bTypeError\b", "TypeError", "Python"),
    (r"\bValueError\b", "ValueError", "Python"),
    (r"\bKeyError\b", "KeyError", "Python"),
    (r"\bAttributeError\b", "AttributeError", "Python"),
    (r"\bIndexError\b", "IndexError", "Python"),
    (r"\bZeroDivisionError\b", "ZeroDivisionError", "Python"),
    (r"\bNameError\b", "NameError", "Python"),
    (r"\bRecursionError\b", "RecursionError", "Python"),
    (r"\bConnectionRefusedError\b", "ConnectionRefusedError", "API"),
    (r"\bConnectionError\b", "ConnectionError", "API"),
    (r"\bTimeoutError\b", "TimeoutError", "API"),
    (r"\bOSError\b", "OSError", "File/System"),
    (r"\bRuntimeError\b", "RuntimeError", "Python"),
    (r"\bValidationError\b", "ValidationError", "FastAPI"),
    (r"\bStreamlitAPIException\b", "StreamlitAPIException", "Streamlit"),
    (r"\bInvalidDimensionException\b", "InvalidDimensionException", "Database"),
    (r"\bOperationalError\b", "OperationalError", "Database"),
]

# Context keywords to override or refine category
CATEGORY_KEYWORDS = [
    ("Git", [r"\bgit\b", r"fatal: not a git repository", r"failed to push", r"merge conflict", r"detached head"]),
    ("Dependency", [r"\bpip\b", r"wheel", r"resolutionimpossible", r"setup\.py", r"requirements\.txt", r"c\+\+ build tools"]),
    ("Environment", [r"\bvenv\b", r"virtualenv", r"conda", r"activate\.ps1", r"executionpolicy", r"python interpreter"]),
    ("FastAPI", [r"\bfastapi\b", r"\buvicorn\b", r"\bstarlette\b", r"pydantic", r"422 unprocessable", r"cors"]),
    ("Streamlit", [r"\bstreamlit\b", r"st\.", r"session_state", r"axioserror"]),
    ("Database", [r"\bchromadb\b", r"\bsqlite3?\b", r"\bcollection\b", r"vectorstore", r"hnsw", r"postgres", r"mongodb"]),
    ("API", [r"requests\.exceptions", r"httpconnectionpool", r"connection refused", r"401 unauthorized", r"404 not found", r"500 internal server error", r"api endpoint"]),
    ("File/System", [r"no such file or directory", r"permission denied", r"pathlib", r"isadirectoryerror"]),
    ("JavaScript", [r"referenceerror", r"typeerror: undefined", r"uncaught syntaxerror", r"npm err", r"node:"]),
]


def classify_error(error_text: str) -> Dict[str, Any]:
    """Classifies the given error text into an error type and domain category.

    Args:
        error_text: Raw error message or traceback text.

    Returns:
        Dictionary with:
        - 'error_type': detected error type name (e.g. 'ModuleNotFoundError')
        - 'category': technical category (e.g. 'Python', 'FastAPI', 'API')
        - 'confidence': confidence score between 0.0 and 1.0
    """
    if not error_text or not isinstance(error_text, str) or not error_text.strip():
        return {
            "error_type": "UnknownError",
            "category": "Other",
            "confidence": 0.0
        }

    text = error_text.strip()
    text_lower = text.lower()

    detected_type = "UnknownError"
    category = "Other"
    confidence = 0.50

    # 1. Match exact error type
    matched_type_category = None
    for pattern, error_name, def_cat in ERROR_TYPE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            detected_type = error_name
            matched_type_category = def_cat
            confidence = 0.85
            break

    # If no standard error type matched, try to extract 'XError' or 'XException'
    if detected_type == "UnknownError":
        generic_match = re.search(r"\b([A-Z][a-zA-Z0-9]+(?:Error|Exception))\b", text)
        if generic_match:
            detected_type = generic_match.group(1)
            confidence = 0.70

    # 2. Refine category based on context keywords
    refined_category = None
    highest_score = 0
    for cat_name, kw_patterns in CATEGORY_KEYWORDS:
        score = sum(1 for kw in kw_patterns if re.search(kw, text_lower))
        if score > highest_score:
            highest_score = score
            refined_category = cat_name

    # Determine final category
    if refined_category:
        category = refined_category
        # If type matched and keyword strongly confirms, boost confidence
        if matched_type_category and (matched_type_category == refined_category or highest_score >= 2):
            confidence = min(0.98, confidence + 0.10)
        elif not matched_type_category:
            confidence = min(0.90, 0.65 + 0.08 * highest_score)
    elif matched_type_category:
        category = matched_type_category
        confidence = min(0.92, confidence)
    else:
        # Default fallback
        category = "Other"
        confidence = 0.35

    return {
        "error_type": detected_type,
        "category": category,
        "confidence": round(confidence, 2)
    }


if __name__ == "__main__":
    samples = [
        "ModuleNotFoundError: No module named 'backend'",
        "OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)",
        "requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8000)",
        "fatal: not a git repository (or any of the parent directories): .git",
        "StreamlitAPIException: Duplicate key 'diagnose_btn'",
        "InvalidDimensionException: Embedding dimension 384 does not match collection dimension 1536",
    ]
    for s in samples:
        res = classify_error(s)
        print(f"Text: '{s[:45]}...' -> Type: {res['error_type']} | Cat: {res['category']} | Conf: {res['confidence']}")
