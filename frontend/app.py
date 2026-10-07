"""Streamlit Frontend Application for AI Troubleshooting Assistant.

Interactive UI for technical error diagnosis, RAG knowledge inspection,
and step-by-step solution visualization.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Troubleshooting Assistant",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Backend API URL from Streamlit secrets (with local fallback)
is_deployed = False
try:
    BACKEND_API_URL = st.secrets["BACKEND_API_URL"].strip().rstrip("/")
    is_deployed = True
except Exception:
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000")).strip().rstrip("/")

# Sidebar Configuration
st.sidebar.title("⚙️ Configuration")

# Allow manual override or display configured backend URL
backend_input = st.sidebar.text_input(
    "Backend API URL",
    value=BACKEND_API_URL,
    help="Configured FastAPI backend URL (via Streamlit secret BACKEND_API_URL or local fallback)"
).strip().rstrip("/")

if backend_input:
    BACKEND_API_URL = backend_input

# Reusable cached health check
@st.cache_data(ttl=15, show_spinner=False)
def fetch_backend_health(url: str):
    """Caches health check for 15 seconds to prevent network lag on UI reruns."""
    try:
        resp = requests.get(f"{url}/health", timeout=3)
        if resp.status_code == 200:
            return True, resp.json()
        return False, {"error": f"Status {resp.status_code}"}
    except Exception as exc:
        return False, {"error": str(exc)}


is_online, health_data = fetch_backend_health(BACKEND_API_URL)
if is_online:
    st.sidebar.success("● Backend Online")
    st.sidebar.caption(
        f"Knowledge Vectors: **{health_data.get('knowledge_base_count', 0)}** chunks\n\n"
        f"Collection: `{health_data.get('collection_name', 'default')}`"
    )
else:
    st.sidebar.error("● Backend Offline")
    if is_deployed or ("127.0.0.1" not in BACKEND_API_URL and "localhost" not in BACKEND_API_URL):
        st.sidebar.caption(
            f"Unable to connect to deployed backend at:\n`{BACKEND_API_URL}`\n\n"
            "Please verify that your deployed FastAPI service is active and running."
        )
    else:
        st.sidebar.caption("Run locally: `python -m uvicorn backend.main:app --reload`")

# Sample Error Presets
st.sidebar.markdown("---")
st.sidebar.subheader("📋 Example Errors")

example_options = {
    "Select an example...": "",
    "Python ModuleNotFoundError": "ModuleNotFoundError: No module named 'backend'",
    "Python Circular ImportError": "ImportError: cannot import name 'retriever' from partially initialized module 'backend.rag'",
    "FastAPI Port Collision": "OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): only one usage of each socket address is normally permitted",
    "Streamlit API Connection Refused": "requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded with url: /troubleshoot (Caused by NewConnectionError: [WinError 10061] No connection could be made)",
    "ChromaDB Dimension Mismatch": "InvalidDimensionException: Embedding dimension 384 does not match collection dimension 1536",
    "File Path Not Found": "FileNotFoundError: [Errno 2] No such file or directory: 'data/documentation/guide.md'",
    "Git Not a Repository": "fatal: not a git repository (or any of the parent directories): .git",
    "Pip Build Wheel Failure": "error: Microsoft Visual C++ 14.0 or greater is required. Get it with 'Microsoft C++ Build Tools'",
}

selected_example = st.sidebar.selectbox(
    "Choose a preset to populate input:",
    options=list(example_options.keys()),
    index=1  # Default to ModuleNotFoundError
)

# Header Section
st.title("🛠️ AI Troubleshooting Assistant")
st.markdown("#### *LLM + RAG Powered Technical Troubleshooting*")
st.markdown(
    "Enter an error message, exception, or stack trace below. The assistant retrieves relevant "
    "technical documentation via **RAG (ChromaDB + sentence-transformers)** and generates an "
    "accurate, step-by-step resolution."
)

st.markdown("---")

# Input Form
col_input, col_config = st.columns([3, 1])

with col_input:
    initial_text = example_options.get(selected_example, "")
    error_input = st.text_area(
        "Enter Technical Error / Stack Trace:",
        value=initial_text,
        height=140,
        placeholder="e.g. ModuleNotFoundError: No module named 'backend'",
        key="error_input_field"
    )

with col_config:
    st.markdown("**Search Settings**")
    top_k = st.slider(
        "Top-K Knowledge Chunks",
        min_value=1,
        max_value=8,
        value=3,
        help="Number of relevant knowledge chunks to retrieve from ChromaDB"
    )
    diagnose_button = st.button("🔍 Diagnose Error", type="primary", use_container_width=True)

# Processing and Results Display
# Handle Diagnose Button Action
if diagnose_button:
    if not error_input or not error_input.strip():
        st.warning("⚠️ Please enter an error message or select an example before diagnosing.")
    else:
        with st.spinner("Analyzing error and querying knowledge base via RAG..."):
            try:
                response = requests.post(
                    f"{BACKEND_API_URL}/troubleshoot",
                    json={"error_text": error_input.strip(), "top_k": top_k},
                    timeout=30
                )
                if response.status_code == 200:
                    st.session_state["diagnosis_data"] = response.json()
                else:
                    st.error(f"Backend API Error ({response.status_code}): {response.text}")
            except requests.exceptions.ConnectionError:
                if is_deployed or ("127.0.0.1" not in BACKEND_API_URL and "localhost" not in BACKEND_API_URL):
                    st.error(
                        f"❌ Unable to connect to the deployed backend server at `{BACKEND_API_URL}`.\n\n"
                        "Please verify that your deployed FastAPI service is active, running, and accessible from Streamlit Cloud."
                    )
                else:
                    st.error(
                        f"❌ Unable to connect to the local backend server at `{BACKEND_API_URL}`.\n\n"
                        "Please ensure the local FastAPI service is running:\n"
                        "```powershell\n"
                        "python -m uvicorn backend.main:app --reload\n"
                        "```"
                    )
            except Exception as exc:
                st.error(f"An unexpected error occurred: {str(exc)}")

# Render Diagnosis Results from Session State
if "diagnosis_data" in st.session_state:
    data = st.session_state["diagnosis_data"]

    st.markdown("---")
    st.subheader("📊 Diagnostic Summary")

    # Classification Badges / Metrics
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    with col_metric1:
        st.metric("Error Type", data.get("error_type", "Unknown"))
    with col_metric2:
        st.metric("Category", data.get("category", "General"))
    with col_metric3:
        conf_pct = int(data.get("confidence", 0.0) * 100)
        st.metric("Classification Confidence", f"{conf_pct}%")

    # High-Level Diagnosis
    st.info(f"**Likely Cause:**\n\n{data.get('diagnosis', 'Analysis pending.')}")

    # Likely Causes List
    causes = data.get("likely_causes", [])
    if causes:
        with st.expander("📌 Root Cause Hypotheses", expanded=True):
            for idx, c in enumerate(causes, 1):
                st.markdown(f"**{idx}.** {c}")

    # Step-by-Step Solution
    st.markdown("### 💡 Step-by-Step Solution")
    solution_markdown = data.get("solution", "No solution generated.")
    st.markdown(solution_markdown)

    # Retrieved Knowledge Sources
    st.markdown("---")
    retrieved = data.get("retrieved_sources", [])
    st.subheader(f"📚 Knowledge Sources Used by RAG ({len(retrieved)} retrieved)")

    if retrieved:
        for idx, doc in enumerate(retrieved, 1):
            source_path = doc.get("source", "Unknown")
            category = doc.get("category", "general")
            distance = doc.get("distance", 0.0)
            similarity_pct = max(0, int((1.0 - distance) * 100))

            with st.expander(f"Source #{idx}: `{source_path}` (Match: ~{similarity_pct}%)", expanded=(idx == 1)):
                st.caption(f"Category: `{category}` | Cosine Distance: `{distance}`")
                st.code(doc.get("content", ""), language="markdown")
    else:
        st.caption("No matching knowledge base documents were retrieved.")
