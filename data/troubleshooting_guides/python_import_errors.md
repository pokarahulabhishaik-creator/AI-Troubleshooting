# Troubleshooting Python ImportError and Circular Imports

## Overview
`ImportError` occurs when an import statement fails to find an attribute, class, or function inside an existing module, or when a circular dependency halts module initialization before names are bound.

## Common Error Signatures
- `ImportError: cannot import name 'X' from partially initialized module 'Y' (most likely due to a circular import)`
- `ImportError: cannot import name 'retriever' from 'backend.rag'`
- `ImportError: attempted relative import with no known parent package`

## Common Causes
1. **Circular Import Dependency**: Module A imports Module B, and Module B directly imports Module A at the top level. When Python initializes Module A, it stops midway to load Module B, which tries to access uninitialized names in Module A.
2. **Module Name Shadowing**: A local file or package shares the exact name of a standard library or third-party package (e.g., naming your file `random.py`, `email.py`, `typing.py`, or `requests.py`).
3. **Attempted Relative Import Outside Package**: Running a submodule directly (`python backend/rag/pipeline.py`) when it uses `from .retriever import ...`. Python treats scripts executed as top-level (`__name__ == '__main__'`) without parent package context.
4. **Typo in Imported Symbol**: The target class or function name is misspelled or was refactored/renamed in the target module.

## Step-by-Step Resolution

### 1. Resolve Circular Imports
- Refactor shared functions, constants, or types into a dedicated base module (e.g., `schemas.py` or `models.py`).
- Use deferred imports: import the needed object inside the specific function or method where it is invoked instead of at the top of the file:
  ```python
  def execute_task():
      from backend.rag.pipeline import run_rag_pipeline
      return run_rag_pipeline(...)
  ```
- Use `if TYPE_CHECKING:` from the `typing` module for static analysis without runtime circular imports.

### 2. Eliminate File Name Shadowing
Check your directory for scripts named after standard libraries:
- Rename `test_requests.py` if it was named `requests.py`.
- Delete any compiled bytecode caches (`__pycache__` and `*.pyc`) after renaming the file.

### 3. Fix Relative Imports Execution
Always execute modules through the `-m` switch from the project root rather than invoking the file directly:
```bash
# Correct
python -m backend.rag.pipeline

# Avoid
python backend/rag/pipeline.py
```

## Verification Steps
Test importing the problematic symbol directly via a single-line command:
```bash
python -c "from backend.rag.retriever import retrieve_documents; print('Import succeeded')"
```
