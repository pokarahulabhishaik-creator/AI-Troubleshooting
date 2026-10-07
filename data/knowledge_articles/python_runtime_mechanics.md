# In-Depth Guide: Python Runtime Mechanics, Imports, and Virtual Environments

## 1. How Python Resolves Module Imports
When Python executes `import backend.rag.retriever`:
1. **Module Cache Check**: Python first inspects `sys.modules`. If `backend.rag.retriever` has already been imported, Python returns the existing cached module reference immediately.
2. **Built-in & Frozen Modules**: Python checks if the name belongs to built-in modules compiled into the Python interpreter binary.
3. **Finder & Loader Inspection**: Python queries its `sys.meta_path` finders. The default `PathFinder` examines each directory in `sys.path`.
4. **Resolution Rules**:
   - For regular packages: A directory containing an `__init__.py` file.
   - For namespace packages (PEP 420): A directory without `__init__.py` spanning one or more paths in `sys.path`.
   - Single-file modules: A file ending in `.py`, `.pyc`, or C extensions (`.pyd` or `.so`).
5. **Execution**: The code within the module is evaluated from top to bottom, creating the module's namespace dictionary `__dict__`.

## 2. The Danger of Working Directory Mismatches
When running Python from the command line:
- `python path/to/script.py` puts `path/to/` at the head of `sys.path`. If your code says `from backend.services import ...`, and you run from inside `backend/`, Python looks for a subdirectory named `backend/backend/` and fails with `ModuleNotFoundError: No module named 'backend'`.
- Running with `-m` (`python -m backend.main`) sets `sys.path[0]` to the current working directory, preserving top-level package boundaries.

## 3. How Virtual Environments Work
A virtual environment is not a full Python installation; it consists of:
- A `pyvenv.cfg` configuration file specifying the home directory of the base Python interpreter.
- A `Scripts/` (Windows) or `bin/` (Unix) directory containing symbolic links or thin wrapper executables for `python.exe` and `pip.exe`.
- A `Lib/site-packages/` directory where packages installed by `pip` reside in isolation from the global Python environment.
When activated, the virtual environment alters the `PATH` environment variable so that invocations of `python` and `pip` resolve to the isolated environment's binaries.
