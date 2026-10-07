# Frequently Asked Troubleshooting Questions (FAQ)

## Q1: Why does Python say "No module named 'backend'" when the folder clearly exists?
**Answer**: Python searches folders listed in `sys.path`. When you run a script using `python backend/main.py`, Python sets `sys.path[0]` to the directory containing `main.py` (`backend/`). In this context, `backend` is the current folder, not a package inside the path. To solve this, run from the project root using `python -m backend.main:app` or export `PYTHONPATH=.`.

## Q2: How do I resolve "Address already in use: Port 8000" on Windows?
**Answer**: Run `Get-NetTCPConnection -LocalPort 8000` in PowerShell to find the `OwningProcess` ID. Then terminate it with `Stop-Process -Id <PID> -Force`. Alternatively, run Uvicorn on another port with `--port 8001`.

## Q3: What is the difference between ModuleNotFoundError and ImportError?
**Answer**: `ModuleNotFoundError` is a subclass of `ImportError`. It specifically means the `.py` file or package directory could not be located anywhere on `sys.path`. A generic `ImportError` usually means the file was found, but a specific class, function, or attribute inside it could not be imported (often due to circular imports or typographical errors).

## Q4: Why does ChromaDB fail with sqlite3 errors on some systems?
**Answer**: ChromaDB requires SQLite 3.35.0 or later to support modern vector metadata operations. On Linux distributions with older system SQLite libraries, you must install `pysqlite3-binary` and override the standard library `sqlite3` before importing ChromaDB.

## Q5: How can I test if my virtual environment has the required packages?
**Answer**: Run `pip list` in your activated terminal, or run `python -c "import fastapi, chromadb, streamlit; print('All packages present!')"`.

## Q6: Why does Streamlit show "AxiosError" or "Connection Refused"?
**Answer**: Streamlit connects via HTTP `requests` to the FastAPI backend. If the backend server (`http://127.0.0.1:8000`) has not been started yet or crashed, Streamlit encounters a connection error. Always start the backend first.
