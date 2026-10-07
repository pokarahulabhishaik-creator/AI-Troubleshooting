# AI Troubleshooting Assistant

An enterprise-ready, LLM and Retrieval-Augmented Generation (RAG) powered technical troubleshooting system designed to automatically diagnose software errors, query an embedded vector database of developer knowledge, and synthesize step-by-step resolution plans.

---

## 📌 Problem Statement
Developers and DevOps engineers frequently encounter runtime errors, configuration mismatches, and stack traces—such as `ModuleNotFoundError`, circular `ImportError`, port collisions (`OSError 10048`), and database driver incompatibilities. Traditional troubleshooting involves manually scouring forums, wading through disparate documentation, or trial-and-error debugging.

The **AI Troubleshooting Assistant** provides automated, context-grounded diagnosis:
1. It ingests technical error logs and stack traces.
2. It classifies the error type and domain category using rule-based and contextual heuristics.
3. It retrieves grounded troubleshooting documentation using dense vector semantic search (Sentence Transformers + ChromaDB).
4. It diagnoses root causes and generates an actionable 6-step solution via an LLM (with zero-failure offline fallback mode).

---

## 🚀 Key Features
- **Semantic RAG Knowledge Base**: High-dimensional vector indexing (`all-MiniLM-L6-v2`) backed by a persistent ChromaDB database.
- **Automated Document Ingestion & Chunking**: Recursive parser supporting `.md` and `.txt` files with sliding window chunking (`CHUNK_SIZE = 500`, `CHUNK_OVERLAP = 100`) and metadata preservation.
- **Independent Error Classifier**: Modular rule and regex classifier detecting standard Python exceptions, frameworks (FastAPI, Streamlit), databases (ChromaDB, SQLite), Git, and networking issues.
- **Grounded Technical Diagnosis**: Root causes and hypotheses directly backed by retrieved documentation snippets, preventing hallucination.
- **Configurable LLM Solution Generator**:
  - Connects to OpenAI, Gemini (OpenAI-compatible), Groq, OpenRouter, or Ollama via standard environment variables.
  - **Graceful Fallback**: If no API key is provided, the system synthesizes a complete 6-part resolution plan directly from retrieved knowledge chunks without crashing.
- **RESTful API Backend**: Built with FastAPI and Pydantic schemas, fully documented with Swagger UI at `/docs`.
- **Interactive Streamlit UI**: User-friendly web interface featuring preset errors, top-K adjustment, metric scorecards, step-by-step guides, and collapsible source inspection cards.
- **Benchmark Evaluation Suite**: Measures Hit@1, Hit@K, and semantic distance metrics across real-world error queries.

---

## 🏗️ System Architecture

```
                       ┌─────────────────────────┐
                       │   USER ERROR / TRACE    │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │    ERROR CLASSIFIER     │
                       │ (Error Type & Category) │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │      RAG PIPELINE       │
                       └────────────┬────────────┘
                                    │
                         Query Embedding (384-dim)
                                    ▼
                       ┌─────────────────────────┐
                       │   CHROMADB VECTORSTORE  │
                       │ (Persistent Collection) │
                       └────────────┬────────────┘
                                    │
                         Top-K Grounded Chunks
                                    ▼
                       ┌─────────────────────────┐
                       │    DIAGNOSIS SERVICE    │
                       │ (Likely Causes & Evid.) │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │   SOLUTION GENERATOR    │
                       │  (LLM or RAG Fallback)  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │     FASTAPI BACKEND     │
                       │  (JSON REST Response)   │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │     STREAMLIT UI        │
                       └─────────────────────────┘
```

---

## 🧠 Retrieval-Augmented Generation (RAG) Explained

RAG bridges the gap between static LLM reasoning and domain-specific knowledge:
1. **Document Ingestion**: Technical articles, error logs, FAQs, and troubleshooting guides in `data/` are parsed into structured documents.
2. **Chunking**: Text is split into overlapping chunks of 500 characters with 100-character overlap to retain contextual continuity across boundaries.
3. **Dense Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` encodes text chunks into 384-dimensional vector representations.
4. **Vector Store**: Vectors, metadata, and original text are indexed into a persistent ChromaDB database (`vectorstore/`).
5. **Similarity Retrieval**: When an error is submitted, its vector embedding is compared against the database using cosine distance to retrieve the most semantically relevant documentation.
6. **Context-Grounded Generation**: The diagnosis and solution generator synthesize technical instructions directly referencing the retrieved evidence.

---

## 💻 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Framework** | FastAPI | High-performance asynchronous REST API |
| **Server** | Uvicorn | ASGI web server implementation |
| **Data Validation** | Pydantic v2 | Schema definition and request/response validation |
| **Frontend UI** | Streamlit | Interactive web application for technical users |
| **Vector Store** | ChromaDB | Embedded vector database with disk persistence |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) | Local dense semantic text embeddings |
| **Configuration** | `python-dotenv` | Environment variable management |
| **HTTP Client** | `requests` | Cross-service communication & LLM completions |

---

## 📁 Project Directory Structure

```
AI_Troubleshooting_Assistant/
│
├── backend/
│   ├── main.py                          # FastAPI application & REST endpoints
│   │
│   ├── rag/
│   │   ├── ingestion.py                 # Document loading from data/
│   │   ├── chunking.py                  # Sliding window text chunker
│   │   ├── embeddings.py                # Embedding model & ChromaDB storage
│   │   ├── retriever.py                 # Semantic similarity search
│   │   └── pipeline.py                  # End-to-end RAG orchestration
│   │
│   ├── services/
│   │   ├── error_classifier.py          # Rule & keyword error classifier
│   │   ├── diagnosis.py                 # Root-cause diagnostic reasoning
│   │   └── solution_generator.py        # LLM / RAG fallback solution engine
│   │
│   └── models/
│       └── schemas.py                   # Pydantic request & response models
│
├── data/
│   ├── error_logs/                      # Runtime stack traces & tracebacks
│   ├── documentation/                   # Official concepts & architecture docs
│   ├── faqs/                            # Common troubleshooting questions
│   ├── troubleshooting_guides/          # Step-by-step guides for known errors
│   └── knowledge_articles/              # In-depth runtime mechanics guides
│
├── vectorstore/                         # ChromaDB persistent database files
│
├── frontend/
│   └── app.py                           # Streamlit user interface
│
├── evaluation/
│   └── rag_evaluation.py                # Retrieval accuracy benchmark suite
│
├── requirements.txt                     # Pinned project dependencies
├── .env                                 # Environment variables (configurable)
├── .gitignore                           # Ignored files (venv, vectorstore, etc.)
└── README.md                            # Comprehensive project documentation
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12 on Windows)
- PowerShell or Terminal

### 2. Create and Activate Virtual Environment
Open PowerShell in the project directory (`D:\AI-Troubleshooting`):

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment on Windows
.\venv\Scripts\Activate.ps1
```

> **Note for PowerShell execution policy**: If script execution is restricted on Windows, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🔧 Configuration (`.env`)

The project contains a `.env` file with configurable settings:

```env
# LLM Provider Configuration (Optional)
# If left as placeholder or empty, the system automatically uses the intelligent RAG-grounded fallback generator.
LLM_PROVIDER=openai
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1

# Backend Server Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_URL=http://127.0.0.1:8000

# Vector Store Configuration
VECTORSTORE_DIR=vectorstore
COLLECTION_NAME=troubleshooting_knowledge
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## 📥 Ingest Knowledge & Build Vector Database

Before querying, index the knowledge documents into ChromaDB:

```powershell
python -m backend.rag.embeddings
```

This reads all markdown and text documents from `data/`, chunks them into 500-character segments with 100-character overlap, generates 384-dimensional embeddings, and writes the persistent index to `vectorstore/`.

---

## 🚀 Running the Application

### 1. Start the FastAPI Backend
In your activated terminal:

```powershell
python -m uvicorn backend.main:app --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### 2. Start the Streamlit Frontend
Open a second terminal, navigate to the project root, activate `venv`, and run:

```powershell
.\venv\Scripts\Activate.ps1
python -m streamlit run frontend/app.py
```

Streamlit will launch automatically in your default browser at `http://localhost:8501`.

---

## ☁️ Cloud Deployment Configuration

When deploying the frontend to **Streamlit Community Cloud** and the backend to a cloud host (such as Render, Railway, Fly.io, or AWS):

### 1. Streamlit Cloud Secrets Configuration
The deployed Streamlit application reads the backend URL directly from Streamlit Secrets:

1. Open your app dashboard on [share.streamlit.io](https://share.streamlit.io).
2. Go to **Settings** -> **Secrets**.
3. Add your deployed FastAPI backend URL:
   ```toml
   BACKEND_API_URL = "https://your-deployed-fastapi-api.onrender.com"
   ```
4. Save the secrets. The deployed frontend will automatically route all health checks and diagnostic requests to your live backend.

### 2. Local vs. Deployed Fallback Behavior
- **Local Development**: When `BACKEND_API_URL` is not defined in Streamlit secrets, the frontend safely falls back to `http://127.0.0.1:8000`.
- **Deployed Production**: When `BACKEND_API_URL` is set, the frontend uses the secret URL and suppresses localhost warnings.

### 3. FastAPI CORS for Cloud Frontends
The FastAPI backend (`backend/main.py`) allows:
- Local development origins: `http://localhost:8501`, `http://127.0.0.1:8501`
- Deployed Streamlit Cloud regex: `^https://.*\.streamlit\.app$`
- Custom origins via the `ALLOWED_ORIGINS` environment variable (e.g. `ALLOWED_ORIGINS=https://my-domain.com`).

---

## 🧪 Benchmark Evaluation

Run the automated evaluation benchmark to measure retrieval accuracy and semantic distance across technical error scenarios:

```powershell
python -m evaluation.rag_evaluation
```

### Metrics Evaluated:
- **Hit@1**: Whether the most relevant document was returned in the #1 rank.
- **Hit@K**: Whether any ground-truth relevant document was present in the top-K results.
- **Mean Cosine Distance**: Quantitative measure of vector proximity (lower = closer match).

---

## 📝 Example Walkthrough

### Example Input:
```text
ModuleNotFoundError: No module named 'backend'
```

### Generated Output:

#### Error Classification:
- **Error Type**: `ModuleNotFoundError`
- **Category**: `Python`
- **Confidence**: `95%`

#### Likely Cause:
Python cannot locate the package `'backend'` because the application was executed from an improper working directory, the virtual environment is not activated, or the package import path is not on `sys.path`.

#### Grounded Step-by-Step Solution:
1. **Navigate to the Project Root Directory**:
   Ensure your shell is positioned in the repository root containing `backend`.
2. **Activate the Virtual Environment**:
   Switch to the isolated environment where your project dependencies reside (`.\venv\Scripts\Activate.ps1`).
3. **Verify Package Existence & Structure**:
   Ensure `backend` exists as a directory with Python files or `__init__.py`.
4. **Run Application with Module Flag (`-m`)**:
   Avoid executing nested scripts directly. Run via Python's module launcher from the root:
   ```bash
   python -m backend.main
   ```
5. **Test the Import**:
   Execute a quick Python one-liner to verify that `backend` can be loaded:
   ```bash
   python -c "import backend; print('Successfully imported backend')"
   ```

#### Knowledge Sources Used by RAG:
- `data/troubleshooting_guides/python_module_not_found.md` (Match: ~88%)
- `data/documentation/python_package_structure.md` (Match: ~79%)
- `data/error_logs/runtime_error_logs.txt` (Match: ~74%)

---

## 🔮 Future Improvements
1. **Fine-Tuned Embeddings**: Train a domain-specific bi-encoder on software engineering stack traces.
2. **Hybrid Search**: Combine BM25 lexical search with dense vector embeddings (Reciprocal Rank Fusion) for exact code identifier matching.
3. **Automated Shell Remediation**: Offer a sandboxed command runner to execute safe verification commands with user approval.
4. **Multi-turn Debugger**: Support interactive conversational sessions where the user can paste subsequent error logs.
