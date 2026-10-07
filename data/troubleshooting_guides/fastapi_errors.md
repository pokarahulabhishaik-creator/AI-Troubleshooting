# Troubleshooting FastAPI and Uvicorn Errors

## Overview
FastAPI applications commonly encounter port conflicts, request schema validation failures, CORS restrictions when contacted from frontend clients, or lifespan lifecycle initialization bugs.

## Common Error Signatures
- `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): only one usage of each socket address (protocol/network address/port) is normally permitted`
- `fastapi.exceptions.RequestValidationError: 422 Unprocessable Entity`
- `Access to fetch at 'http://127.0.0.1:8000/troubleshoot' from origin 'http://localhost:8501' has been blocked by CORS policy`
- `405 Method Not Allowed`
- `404 Not Found`

## Common Causes
1. **Port 8000 Conflict**: A previously running instance of Uvicorn or another background server is still occupying port 8000.
2. **Missing CORS Middleware**: The FastAPI backend lacks `CORSMiddleware` configuration, causing modern browsers to reject HTTP requests originating from Streamlit or other web interfaces.
3. **Pydantic Validation Failures**: The JSON body sent in POST requests does not match the schema fields (e.g., missing required fields, incorrect data types).
4. **Incorrect HTTP Method**: Sending a GET request to a route defined exclusively as POST, or vice versa.

## Step-by-Step Resolution

### 1. Resolve Port 8000 Conflict on Windows
Identify and terminate the lingering process holding port 8000:
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# Terminate process by PID
Stop-Process -Id <PID> -Force
```
Alternatively, specify a different port when launching Uvicorn:
```powershell
python -m uvicorn backend.main:app --port 8080 --reload
```

### 2. Configure CORS in FastAPI
Add the standard CORS middleware to your FastAPI app:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Handle 422 Unprocessable Entity
Inspect the error payload in the response body. Ensure that your Pydantic model defines default values or optional fields where appropriate:
```python
from pydantic import BaseModel, Field

class TroubleshootRequest(BaseModel):
    error_text: str = Field(..., description="The error message to diagnose")
    top_k: int = Field(default=3, ge=1, le=10)
```

## Verification Steps
1. Navigate to `http://127.0.0.1:8000/docs` in your browser to inspect interactive Swagger documentation.
2. Test the health endpoint:
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
   ```
