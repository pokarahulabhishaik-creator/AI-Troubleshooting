# Troubleshooting Python ModuleNotFoundError

## Overview
`ModuleNotFoundError: No module named '<module_name>'` is raised when Python's import system attempts to import a module or package that cannot be located in any of the search paths registered in `sys.path`.

## Error Signatures
- `ModuleNotFoundError: No module named 'backend'`
- `ModuleNotFoundError: No module named 'requests'`
- `ModuleNotFoundError: No module named 'fastapi'`
- `ModuleNotFoundError: No module named 'chromadb'`

## Common Causes
1. **Incorrect Current Working Directory**: The application is executed from a subfolder rather than the project root directory, meaning top-level packages are not on `sys.path`.
2. **Missing Virtual Environment Activation**: The dependencies were installed into a virtual environment (`venv`), but the active shell is using the global system Python interpreter where the package is absent.
3. **Package Not Installed**: The third-party library has not been installed using `pip install <package>`.
4. **Incorrect Import Path or Typo**: The code uses a relative import where an absolute import is required, or the package name is misspelled.
5. **Missing Package Markers or Structure**: In traditional Python packaging, missing `__init__.py` files or improper layout prevents Python from recognizing folders as packages.
6. **Interpreter Mismatch in IDE**: The IDE (VS Code, PyCharm) is configured to use a different Python interpreter than the one where dependencies were installed.

## Step-by-Step Resolution

### 1. Run from the Project Root Directory
Always execute your Python script or server from the repository root:
```bash
# Correct execution from project root
cd /path/to/project_root
python -m backend.main
```
Avoid navigating into `backend/` and running `python main.py`, because Python sets `sys.path[0]` to the directory of the script being run (`backend/`), which removes the root from the import search path.

### 2. Verify and Activate the Virtual Environment
Ensure your terminal session has activated the designated virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  source venv/bin/activate
  ```
Check which interpreter is active:
```bash
# Windows
Get-Command python | Select-Object Source
# Linux / macOS
which python
```

### 3. Verify Package Installation
Confirm that the module is installed in the current environment:
```bash
pip list
# or check directly
python -c "import <module_name>; print(<module_name>.__file__)"
```
If missing, install it:
```bash
pip install <module_name>
# or install project requirements
pip install -r requirements.txt
```

### 4. Check Package Structure and __init__.py
Ensure your project contains clean package boundaries:
```
project_root/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── rag/
│       ├── __init__.py
│       └── retriever.py
```
While Python 3.3+ supports implicit namespace packages without `__init__.py`, adding empty `__init__.py` files explicitly marks directories as packages and avoids resolution ambiguities across different tools.

### 5. Check or Export PYTHONPATH
If your code layout requires importing modules from outside the current working directory, explicitly add the project root to `PYTHONPATH`:
- **Windows PowerShell**:
  ```powershell
  $env:PYTHONPATH = (Get-Location).Path
  ```
- **Linux / macOS**:
  ```bash
  export PYTHONPATH=.
  ```

## Verification Steps
1. In your activated environment, run:
   ```bash
   python -c "import backend; print('Import successful!')"
   ```
2. Start the service using the module runner flag:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
