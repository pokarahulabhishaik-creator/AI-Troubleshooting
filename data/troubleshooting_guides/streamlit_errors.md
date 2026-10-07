# Troubleshooting Streamlit Errors

## Overview
Streamlit re-runs the entire Python script on every user interaction. Common issues include state management conflicts, duplicate widget keys, port conflicts, caching issues, or failure to communicate with backend APIs.

## Common Error Signatures
- `StreamlitAPIException: There are multiple identical st.button widgets with the same generated key.`
- `requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded`
- `KeyError: 'st.session_state has no key "result"'`
- `AxiosError: Request failed with status code 500`

## Common Causes
1. **Duplicate Widget Keys**: Creating multiple widgets of the same type without unique `key` parameters in loops or conditional blocks.
2. **Backend Server Down**: The Streamlit frontend is attempting to query `http://127.0.0.1:8000/troubleshoot` before the FastAPI backend is launched.
3. **Session State Initialization**: Reading from `st.session_state["key"]` before it has been set or initialized.
4. **Caching Invalidation**: Using `@st.cache_data` or `@st.cache_resource` on functions with unhashable arguments.

## Step-by-Step Resolution

### 1. Ensure Backend is Running First
Always verify that FastAPI is running prior to making requests from Streamlit:
```powershell
# In terminal 1 (FastAPI backend)
python -m uvicorn backend.main:app --reload

# In terminal 2 (Streamlit frontend)
python -m streamlit run frontend/app.py
```

### 2. Handle API Connection Failures Gracefully
Wrap HTTP requests to FastAPI in a try-except block and display user-friendly warnings:
```python
import requests
import streamlit as st

try:
    response = requests.post(
        f"{backend_url}/troubleshoot",
        json={"error_text": user_error, "top_k": top_k},
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to backend API at " + backend_url + ". Please make sure Uvicorn is running.")
except requests.exceptions.RequestException as e:
    st.error(f"Request failed: {str(e)}")
```

### 3. Provide Unique Widget Keys
Assign explicit `key` parameters:
```python
st.text_area("Error Message", key="error_input_area")
st.button("Diagnose Error", key="diagnose_btn")
```

## Verification Steps
1. Open `http://localhost:8501` in your browser.
2. Verify frontend renders without session state exceptions.
