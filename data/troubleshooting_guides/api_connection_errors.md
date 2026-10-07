# Troubleshooting HTTP and API Connection Errors

## Overview
Network errors during API communication typically arise from unreachable servers, incorrect ports, timeout expirations, missing environment variables, or SSL handshakes.

## Common Error Signatures
- `requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded with url`
- `requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='api.openai.com', port=443): Request timed out.`
- `urllib3.exceptions.NewConnectionError: Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it`
- `HTTPError: 401 Client Error: Unauthorized for url`
- `HTTPError: 429 Client Error: Too Many Requests`

## Common Causes
1. **Target Server Not Running**: The client attempts to query a local API (e.g., FastAPI on port 8000) before starting the server.
2. **Incorrect URL or Protocol**: Mistyping `http://` as `https://` on a local development server or using the wrong port.
3. **Invalid or Missing API Key**: Calling an LLM API without providing a valid API key in environment variables or headers, returning 401 Unauthorized.
4. **Rate Limiting / Quota Exhaustion**: Hitting provider rate limits (429 Too Many Requests) or lacking account credits.
5. **No Timeout Specified**: Making requests without a `timeout` argument causing threads to hang indefinitely if the network drops.

## Step-by-Step Resolution

### 1. Check If Local Service Is Listening
Verify whether the target host and port are active:
```powershell
# Windows PowerShell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8000
```
If `TcpTestSucceeded` is `False`, launch the backend server first.

### 2. Implement Resilient Requests with Timeout and Retry Logic
Always set timeouts and catch specific network exceptions:
```python
import requests

try:
    response = requests.post(
        "http://127.0.0.1:8000/troubleshoot",
        json={"error_text": "sample error", "top_k": 3},
        timeout=(5.0, 30.0) # 5s connect, 30s read
    )
    response.raise_for_status()
except requests.exceptions.ConnectionError:
    print("Backend server is offline or unreachable.")
except requests.exceptions.Timeout:
    print("Request timed out.")
except requests.exceptions.HTTPError as err:
    print(f"HTTP error: {err.response.status_code} - {err.response.text}")
```

### 3. Handle 401 and 429 Status Codes Gracefully
When calling external LLM providers:
- Check that `.env` is loaded using `python-dotenv`:
  ```python
  from dotenv import load_dotenv
  import os
  load_dotenv()
  api_key = os.getenv("LLM_API_KEY")
  ```
- If API key is invalid or rate limited, gracefully fall back to local rule-based or RAG-synthesized responses without crashing the application.

## Verification Steps
Test endpoint reachability using Python:
```python
import requests
res = requests.get("http://127.0.0.1:8000/health", timeout=5)
print(res.status_code, res.json())
```
