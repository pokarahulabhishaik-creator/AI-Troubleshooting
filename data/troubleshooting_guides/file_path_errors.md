# Troubleshooting File and Path Errors in Python

## Overview
File system errors in Python typically stem from relative path resolution relative to the current working directory, path separator mismatches between Windows and POSIX systems, or permission restrictions.

## Common Error Signatures
- `FileNotFoundError: [Errno 2] No such file or directory: 'data/documentation/guide.md'`
- `PermissionError: [Errno 13] Permission denied: 'vectorstore/chroma.sqlite3'`
- `IsADirectoryError: [Errno 21] Is a directory`
- `SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position...`

## Common Causes
1. **Misunderstanding Relative Paths**: Relative paths (e.g., `'data/documentation'`) are resolved relative to `os.getcwd()` (where the command was initiated), NOT relative to the script file location.
2. **Windows Backslash Escape Sequences**: Writing raw Windows file paths like `"C:\Users\name\test"` in Python source code triggers unicode escape sequence errors because `\t`, `\n`, `\u` are escape characters.
3. **File Lock or Permissions**: SQLite or vector database files opened by another running process cannot be modified or deleted on Windows.
4. **Missing Parent Directories**: Writing a file using `open("path/to/file.txt", "w")` when `path/to` does not yet exist.

## Step-by-Step Resolution

### 1. Robust Path Construction with pathlib
Always use `pathlib.Path` with `resolve()` or `__file__`-relative anchoring:
```python
from pathlib import Path

# Anchor to the project root or current module
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
```

### 2. Prevent Windows Unicode Escape Errors
Use forward slashes or raw strings for Windows paths:
```python
# Recommended
path = Path("d:/AI-Troubleshooting/vectorstore")
# Or raw string
path = Path(r"d:\AI-Troubleshooting\vectorstore")
```

### 3. Ensure Parent Directories Exist Before Writing
```python
from pathlib import Path

output_path = Path("output/results.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text("{}", encoding="utf-8")
```

### 4. Explicitly Specify UTF-8 Encoding
Always set `encoding="utf-8"` when reading and writing text files on Windows to prevent `UnicodeDecodeError` caused by Windows CP-1252 default encoding:
```python
with open("data/file.txt", "r", encoding="utf-8") as f:
    content = f.read()
```

## Verification Steps
Check path existence and current working directory:
```python
import os
from pathlib import Path
print("Current Working Directory:", os.getcwd())
print("Data directory exists:", Path("data").exists())
```
