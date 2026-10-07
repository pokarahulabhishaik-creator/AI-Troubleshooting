# Python Packaging, Directory Layout, and Import Mechanics

## Package Mechanics and sys.path
When an import statement is evaluated in Python, the interpreter searches directories in the following order:
1. `sys.path[0]`: The directory containing the input script that was used to invoke the interpreter (or current working directory if invoked interactively or with `-m`).
2. `PYTHONPATH`: Directories defined in the environment variable.
3. Standard library directories: Built-in Python modules.
4. Site-packages: Third-party packages installed in the virtual environment or global Python.

## Standard Application Layout
A standard scalable Python project layout:
```
AI_Troubleshooting_Assistant/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── pipeline.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── error_classifier.py
│   │   ├── diagnosis.py
│   │   └── solution_generator.py
│   └── models/
│       ├── __init__.py
│       └── schemas.py
├── frontend/
│   └── app.py
├── requirements.txt
└── .env
```

## Absolute vs Relative Imports
- **Absolute imports** specify the complete path from the project root:
  ```python
  from backend.rag.retriever import retrieve_documents
  from backend.models.schemas import TroubleshootRequest
  ```
  Absolute imports are preferred because they are explicit, unambiguous, and work consistently when executed from the project root.
- **Relative imports** use leading dots to indicate the current or parent package:
  ```python
  from .embeddings import get_embedding_model
  from ..models.schemas import TroubleshootRequest
  ```
  Relative imports require the module to be loaded as part of a package. Direct invocation (`python file.py`) will fail with `ImportError: attempted relative import with no known parent package`.

## Best Practices
1. Run everything as modules using `python -m <module_name>` from the root directory.
2. Maintain clear separation of concerns (e.g., schemas in `models/`, business logic in `services/`, data retrieval in `rag/`).
3. Avoid modifying `sys.path` dynamically with `sys.path.append(...)` whenever possible, as it introduces brittle environment-dependent paths.
